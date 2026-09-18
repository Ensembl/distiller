export type StoreChange = {
  target: object;
  key: PropertyKey;
  previousValue: unknown;
  value: unknown;
};

export type StoreListener = (change: StoreChange) => void;

export interface Store<T extends object> {
  readonly state: T;
  subscribe(listener: StoreListener): () => void;
}

export function createStore<T extends object>(initialState: T): Store<T> {
  const listeners = new Set<StoreListener>();
  const proxies = new WeakMap<object, object>();

  const notify = (change: StoreChange): void => {
    for (const listener of listeners) {
      listener(change);
    }
  };

  const wrap = <V>(value: V): V => {
    if (value === null || typeof value !== "object") {
      return value;
    }

    const objectValue = value;
    const existingProxy = proxies.get(objectValue);

    if (existingProxy) {
      return existingProxy as V;
    }

    const proxy = new Proxy(objectValue, {
      get(target, key, receiver) {
        return wrap(Reflect.get(target, key, receiver));
      },

      set(target, key, nextValue, receiver) {
        const previousValue = Reflect.get(target, key, receiver);

        if (Object.is(previousValue, nextValue)) {
          return true;
        }

        const updated = Reflect.set(target, key, nextValue, receiver);

        if (updated) {
          notify({
            target: receiver,
            key,
            previousValue,
            value: nextValue,
          });
        }

        return updated;
      }
    });

    proxies.set(objectValue, proxy);
    return proxy as V;
  };

  return {
    state: wrap(initialState),

    subscribe(listener: StoreListener): () => void {
      listeners.add(listener);

      return () => {
        listeners.delete(listener);
      };
    },
  };
}