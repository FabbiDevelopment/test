interface TokenStorage {
  removeItem: (key: string) => void;
}

interface QueryCache {
  removeQueries: () => unknown;
}

export function clearUserSession(
  storage: TokenStorage,
  queryCache: QueryCache
): void {
  storage.removeItem("access_token");
  storage.removeItem("refresh_token");
  queryCache.removeQueries();
}
