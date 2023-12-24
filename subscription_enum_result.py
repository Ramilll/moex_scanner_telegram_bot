from enum import Enum


class SubscriptionUserToCryptoResult(Enum):
    Ok = 1
    NoSuchCrypto = 2
    AlreadySubscribed = 3


class UnsubscriptionUserFromCryptoResult(Enum):
    Ok = 1
    NotSubscribed = 2
