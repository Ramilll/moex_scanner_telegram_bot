Этот бот – мониторинг цен на токены с использованием данных с CoinMarketCap. Бот уведомляет пользователей о скачках цен на выбранные ими токены.

**Тг бот:**
- *Функционал:*
  - `/subscribe <имена-токенов> <через-пробел>` – подписаться на токены <имена-токенов> <через-пробел>. Если пользователь уже подписан на такие токены, повторно бот подписывать не будет.
  - `/unsubscribe <имена-токенов> <через-пробел>` – отписаться от токены <имена-токенов> <через-пробел>. Если пользователь на какие-то из них не подписан, бот сообщит об этом.
  - `/my_crypto` - вывод списка токенов, на которые пользователь подписан.
  - `/help` - вывод сообщения с подсказками.
- умеет писать нескольким пользователям одновременно
- скачок цены, который бот отслеживает – 0.01% за 10 секунд
