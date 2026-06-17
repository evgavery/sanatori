<?php
/**
 * Шаблон конфига для lead.php.
 *
 * Что делать:
 *   1. Скопировать в реальный config.php ВЫШЕ public_html (на reg.ru — в ~/санаториифнпр.рф/config.php).
 *      Этот путь не доступен по HTTP, токен бота не утечёт.
 *   2. Подставить токен бота и chat_id (см. docs/credentials-regru.md).
 *   3. Этот пример (config.example.php) пустой — его можно держать рядом с lead.php в public_html,
 *      ничего секретного он не содержит.
 */

return [
    // Токен Telegram-бота (@BotFather). Без него уведомления в Telegram не пойдут.
    'telegram_token'   => '',

    // chat_id получателей в Telegram. Можно одно значение (строка) или список (массив):
    //   'telegram_chat_id' => '123456789',
    //   'telegram_chat_id' => ['123456789', '-100123456789'],  // личка + группа
    // Группе чтобы получать сообщения, надо добавить бота в группу. У группы chat_id отрицательный.
    // Как получить — см. docs/credentials-regru.md.
    'telegram_chat_id' => '',

    // Email-получатели. Так же — один адрес (строка) или несколько (массив).
    //   'email_to' => 'zayavki@…',
    //   'email_to' => ['zayavki@…', 'manager@…'],
    'email_to'         => 'zayavki@xn--80aayawdelfebp4a.xn--p1ai',

    // От какого адреса шлём. Должен быть на нашем домене — иначе попадёт в спам (SPF/DKIM).
    'email_from'       => 'noreply@xn--80aayawdelfebp4a.xn--p1ai',

    // Папка для json заявок. По умолчанию — соседняя папка leads/ (выше public_html).
    'leads_dir'        => __DIR__ . '/leads',

    // Разрешённые источники запросов. Пустой массив = принимаем отовсюду.
    'allowed_origins'  => [
        'https://xn--80aayawdelfebp4a.xn--p1ai',
        'https://санаториифнпр.рф',
    ],
];
