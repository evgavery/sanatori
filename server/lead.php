<?php
declare(strict_types=1);

/**
 * Приёмник заявок с формы.
 *
 * Куда класть на сервере (reg.ru / ispmanager):
 *   /home/<user>/<domain>/public_html/lead.php   ← этот файл
 *   /home/<user>/<domain>/config.php             ← секреты (выше public_html, не доступен по URL)
 *   /home/<user>/<domain>/leads/                 ← сюда складываются json заявок (создаётся автоматически)
 *
 * Соответствие 242-ФЗ: заявка сначала сохраняется в файл на российском сервере,
 * только потом форвардится в Telegram/на почту как уведомления.
 */

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    http_response_code(405);
    exit(json_encode(['ok' => false, 'error' => 'method_not_allowed']));
}

// --- Загрузка конфига (вне веб-рута) ---
$configPath = __DIR__ . '/../config.php';
if (!is_file($configPath)) {
    http_response_code(500);
    error_log('[lead] config.php не найден: ' . $configPath);
    exit(json_encode(['ok' => false, 'error' => 'server_config_missing']));
}
$cfg = require $configPath;

// --- Проверка Origin (если задан список разрешённых) ---
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
$allowed = $cfg['allowed_origins'] ?? [];
if ($origin !== '' && !empty($allowed) && !in_array($origin, $allowed, true)) {
    http_response_code(403);
    exit(json_encode(['ok' => false, 'error' => 'origin_not_allowed']));
}

// --- Поля формы ---
$pick = static function (string $key, int $max = 500): string {
    $v = (string)($_POST[$key] ?? '');
    $v = trim($v);
    if (mb_strlen($v) > $max) $v = mb_substr($v, 0, $max);
    return $v;
};

// honeypot: легитимный фронт стирает поле перед отправкой; заполнено только ботом.
if ($pick('company', 100) !== '') {
    // тихо «успех», чтобы бот не пробовал снова.
    exit(json_encode(['ok' => true]));
}

$name     = $pick('name', 100);
$phone    = $pick('phone', 30);
$consent  = $pick('consent', 10);
$sanat    = $pick('sanatorium', 200);
$method   = $pick('contact_method', 50);
$comment  = $pick('comment', 2000);

$pageUrl  = $pick('page_url', 500);
$referrer = $pick('referrer', 500);
$submitted = $pick('submitted_at', 40) ?: date('c');

if ($name === '' || $phone === '' || $consent === '') {
    http_response_code(400);
    exit(json_encode(['ok' => false, 'error' => 'missing_required']));
}

$phoneDigits = preg_replace('/\D+/', '', $phone) ?? '';
if (strlen($phoneDigits) < 10) {
    http_response_code(400);
    exit(json_encode(['ok' => false, 'error' => 'bad_phone']));
}

// --- Запись заявки в файл (первичное хранение в РФ) ---
$leadsDir = rtrim((string)($cfg['leads_dir'] ?? (__DIR__ . '/../leads')), '/');
if (!is_dir($leadsDir)) @mkdir($leadsDir, 0750, true);

$id = date('Ymd_His') . '_' . substr(bin2hex(random_bytes(4)), 0, 6);
$payload = [
    'id'             => $id,
    'submitted_at'   => $submitted,
    'name'           => $name,
    'phone'          => $phone,
    'phone_digits'   => $phoneDigits,
    'sanatorium'     => $sanat,
    'contact_method' => $method,
    'comment'        => $comment,
    'page_url'       => $pageUrl,
    'referrer'       => $referrer,
    'ip'             => $_SERVER['REMOTE_ADDR'] ?? '',
    'user_agent'     => substr((string)($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 300),
];

$saved = @file_put_contents(
    $leadsDir . '/' . $id . '.json',
    json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)
);
if ($saved === false) {
    error_log('[lead] не удалось записать заявку: ' . $id . ' в ' . $leadsDir);
}

// --- Уведомления (best effort; не падаем, если канал лёг) ---
$sent = ['telegram' => 0, 'email' => 0];

// Telegram — поддерживаем как одно значение (строка), так и список (массив).
if (!empty($cfg['telegram_token'])) {
    $chatIds = normalize_recipients($cfg['telegram_chat_id'] ?? []);
    $text = build_telegram_text($payload);
    foreach ($chatIds as $cid) {
        try {
            send_telegram($cfg['telegram_token'], $cid, $text);
            $sent['telegram']++;
        } catch (Throwable $e) {
            error_log('[lead] telegram chat=' . $cid . ': ' . $e->getMessage());
        }
    }
}

// Email — то же, можно один адрес или массив.
$emails = normalize_recipients($cfg['email_to'] ?? []);
if (!empty($emails)) {
    $from = (string)($cfg['email_from'] ?? ('noreply@' . ($_SERVER['HTTP_HOST'] ?? 'localhost')));
    foreach ($emails as $addr) {
        try {
            send_email($addr, $from, $payload);
            $sent['email']++;
        } catch (Throwable $e) {
            error_log('[lead] email to=' . $addr . ': ' . $e->getMessage());
        }
    }
}

exit(json_encode(['ok' => true, 'id' => $id, 'sent' => $sent]));

// --- helpers ---

/** Превратить значение конфига в список адресатов (строка → [строка], массив остаётся массивом). */
function normalize_recipients($v): array
{
    if (is_string($v)) $v = [$v];
    if (!is_array($v)) return [];
    $out = [];
    foreach ($v as $item) {
        $s = trim((string)$item);
        if ($s !== '') $out[] = $s;
    }
    return $out;
}

function build_telegram_text(array $p): string
{
    $esc = static fn(string $s): string => htmlspecialchars($s, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    $lines = [
        '🛎 <b>Новая заявка с сайта</b>',
        '',
        '<b>Имя:</b> ' . $esc($p['name']),
        '<b>Телефон:</b> ' . $esc($p['phone']),
    ];
    if ($p['sanatorium'] !== '')     $lines[] = '<b>Санаторий:</b> ' . $esc($p['sanatorium']);
    if ($p['contact_method'] !== '') $lines[] = '<b>Связь:</b> ' . $esc($p['contact_method']);
    if ($p['comment'] !== '')        $lines[] = '<b>Комментарий:</b> ' . $esc($p['comment']);
    $lines[] = '';
    $lines[] = '<i>' . $esc($p['submitted_at']) . '</i>';
    if ($p['page_url'] !== '') $lines[] = '<i>' . $esc($p['page_url']) . '</i>';
    return implode("\n", $lines);
}

function send_telegram(string $token, string $chatId, string $text): void
{
    $url = "https://api.telegram.org/bot{$token}/sendMessage";
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => http_build_query([
            'chat_id'                  => $chatId,
            'text'                     => $text,
            'parse_mode'               => 'HTML',
            'disable_web_page_preview' => true,
        ]),
    ]);
    $resp = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err  = curl_error($ch);
    curl_close($ch);
    if ($resp === false || $code !== 200) {
        throw new RuntimeException("telegram http={$code} err={$err} body={$resp}");
    }
}

function send_email(string $to, string $from, array $p): void
{
    $subject = '=?UTF-8?B?' . base64_encode('Заявка с сайта: ' . ($p['name'] ?: '—')) . '?=';

    $body  = "Поступила заявка с сайта санаториифнпр.рф\n\n";
    $body .= "Имя:           {$p['name']}\n";
    $body .= "Телефон:       {$p['phone']}\n";
    if ($p['sanatorium'] !== '')     $body .= "Санаторий:     {$p['sanatorium']}\n";
    if ($p['contact_method'] !== '') $body .= "Способ связи:  {$p['contact_method']}\n";
    if ($p['comment'] !== '')        $body .= "Комментарий:   {$p['comment']}\n";
    $body .= "\n— служебное —\n";
    $body .= "ID:            {$p['id']}\n";
    $body .= "Время:         {$p['submitted_at']}\n";
    $body .= "Страница:      {$p['page_url']}\n";
    $body .= "Реферер:       {$p['referrer']}\n";
    $body .= "IP:            {$p['ip']}\n";
    $body .= "User-Agent:    {$p['user_agent']}\n";

    $headers  = "From: {$from}\r\n";
    $headers .= "Reply-To: {$from}\r\n";
    $headers .= "Content-Type: text/plain; charset=UTF-8\r\n";
    $headers .= "MIME-Version: 1.0\r\n";
    $headers .= "X-Mailer: lead.php\r\n";

    if (!@mail($to, $subject, $body, $headers)) {
        throw new RuntimeException('mail() returned false');
    }
}
