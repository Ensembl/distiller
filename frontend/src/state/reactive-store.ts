export type StoreChange =
  | {
      type: 'set';
      target: object;
      key: PropertyKey;
      previousValue: unknown;
      value: unknown;
    }
  | {
      type: 'delete';
      target: object;
      key: PropertyKey;
      previousValue: unknown;
      value: undefined;
    };

export type StoreListener = (change: StoreChange) => void;
export type StoreSubscription = { unsubscribe: () => void };

export interface Store<T extends object> {
  readonly state: T;
  subscribe(listener: StoreListener): StoreSubscription;
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
            type: 'set',
            target: receiver,
            key,
            previousValue,
            value: nextValue,
          });
        }

        return updated;
      },

      deleteProperty(target, key) {
        if (!Reflect.has(target, key)) {
          return true;
        }

        const previousValue = Reflect.get(target, key);
        const deleted = Reflect.deleteProperty(target, key);

        if (deleted) {
          notify({
            type: 'delete',
            target: proxy,
            key,
            previousValue,
            value: undefined,
          });
        }

        return deleted;
      }
    });

    proxies.set(objectValue, proxy);
    return proxy as V;
  };

  return {
    state: wrap(initialState),

    subscribe(listener: StoreListener) {
      listeners.add(listener);

      return {
        unsubscribe: () => {
          listeners.delete(listener);
        }
      };
    },
  };
}
