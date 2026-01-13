/**
 * Account mapping utilities and hooks
 *
 * Centralizes all account ID <-> name conversion logic
 */

// Account ID constants
export const ACCOUNT_IDS = {
  BANK: 1,
  WALLET: 2,
  EXCHANGE_USD: 3,
  EXCHANGE_BTC: 4,
  EXTERNAL: 99,
} as const;

// Account names as they appear in the UI
export const ACCOUNT_NAMES = {
  [ACCOUNT_IDS.BANK]: 'Bank',
  [ACCOUNT_IDS.WALLET]: 'Wallet',
  [ACCOUNT_IDS.EXCHANGE_USD]: 'Exchange',
  [ACCOUNT_IDS.EXCHANGE_BTC]: 'Exchange',
  [ACCOUNT_IDS.EXTERNAL]: 'External',
} as const;

/**
 * Convert account ID to display name
 */
export function accountIdToName(id: number | null): string {
  if (id === null) return 'N/A';
  return ACCOUNT_NAMES[id as keyof typeof ACCOUNT_NAMES] || `Acct #${id}`;
}

/**
 * Convert account type string to account ID for form submissions
 */
export function accountTypeToId(
  accountType: AccountType,
  currency?: Currency
): number {
  switch (accountType) {
    case 'Bank':
      return ACCOUNT_IDS.BANK;
    case 'Wallet':
      return ACCOUNT_IDS.WALLET;
    case 'Exchange':
      return currency === 'BTC' ? ACCOUNT_IDS.EXCHANGE_BTC : ACCOUNT_IDS.EXCHANGE_USD;
    case 'External':
      return ACCOUNT_IDS.EXTERNAL;
    default:
      return ACCOUNT_IDS.EXTERNAL;
  }
}

/**
 * Convert account ID to account type for form display
 */
export function accountIdToType(id: number | null): AccountType {
  if (id === null) return 'External';
  switch (id) {
    case ACCOUNT_IDS.BANK:
      return 'Bank';
    case ACCOUNT_IDS.WALLET:
      return 'Wallet';
    case ACCOUNT_IDS.EXCHANGE_USD:
    case ACCOUNT_IDS.EXCHANGE_BTC:
      return 'Exchange';
    case ACCOUNT_IDS.EXTERNAL:
      return 'External';
    default:
      return 'External';
  }
}

/**
 * Get account IDs for a transaction type
 */
export function getAccountMapping(
  type: TransactionType,
  options: {
    account?: AccountType;
    currency?: Currency;
    fromAccount?: AccountType;
    toAccount?: AccountType;
    fromCurrency?: Currency;
    toCurrency?: Currency;
  }
): IAccountMapping {
  const {
    account,
    currency,
    fromAccount,
    toAccount,
    fromCurrency,
    toCurrency,
  } = options;

  switch (type) {
    case 'Deposit':
      return {
        from_account_id: ACCOUNT_IDS.EXTERNAL,
        to_account_id: accountTypeToId(account || 'Bank', currency),
      };

    case 'Withdrawal':
      return {
        from_account_id: accountTypeToId(account || 'Bank', currency),
        to_account_id: ACCOUNT_IDS.EXTERNAL,
      };

    case 'Transfer':
      return {
        from_account_id: accountTypeToId(fromAccount || 'Bank', fromCurrency),
        to_account_id: accountTypeToId(toAccount || 'Exchange', toCurrency),
      };

    case 'Buy':
      return {
        from_account_id: ACCOUNT_IDS.EXCHANGE_USD,
        to_account_id: ACCOUNT_IDS.EXCHANGE_BTC,
      };

    case 'Sell':
      return {
        from_account_id: ACCOUNT_IDS.EXCHANGE_BTC,
        to_account_id: ACCOUNT_IDS.EXCHANGE_USD,
      };

    default:
      return {
        from_account_id: ACCOUNT_IDS.EXTERNAL,
        to_account_id: ACCOUNT_IDS.EXTERNAL,
      };
  }
}

/**
 * Resolve display account label for a transaction
 */
export function resolveDisplayAccount(tx: ITransaction): string {
  const { type, from_account_id, to_account_id } = tx;

  switch (type) {
    case 'Deposit':
      return accountIdToName(to_account_id);
    case 'Withdrawal':
      return accountIdToName(from_account_id);
    case 'Transfer':
      return `${accountIdToName(from_account_id)} -> ${accountIdToName(to_account_id)}`;
    case 'Buy':
    case 'Sell':
      return 'Exchange';
    default:
      return 'Unknown';
  }
}

/**
 * Check if an account ID is a USD account
 */
export function isUsdAccount(id: number | null): boolean {
  return id === ACCOUNT_IDS.BANK || id === ACCOUNT_IDS.EXCHANGE_USD;
}

/**
 * Check if an account ID is a BTC account
 */
export function isBtcAccount(id: number | null): boolean {
  return id === ACCOUNT_IDS.WALLET || id === ACCOUNT_IDS.EXCHANGE_BTC;
}

/**
 * Get currency for an account ID
 */
export function getAccountCurrency(id: number | null): Currency {
  return isUsdAccount(id) ? 'USD' : 'BTC';
}
