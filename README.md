This bot is a token price monitoring system using data from CoinMarketCap. The bot notifies users about price spikes for their selected tokens.

**Telegram bot:**
- *Features:*
  - /subscribe <token-names> <space-separated> – subscribe to tokens <token-names> <space-separated>. If the user is already subscribed to some of these tokens, the bot will not subscribe them again.
  - /unsubscribe <token-names> <space-separated> – unsubscribe from tokens <token-names> <space-separated>. If the user is not subscribed to some of these tokens, the bot will notify them.
  - /my_crypto – display the list of tokens the user is subscribed to.
  - /help – display a message with instructions.
- The price spike that the bot monitors is 0.01% over 10 seconds.

