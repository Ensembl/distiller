# Reactive store

Date: 2026-09-18

Lit-based components have reactive properties and reactive state; but in order to share the state across the different components of data distiller that need it, and to prevent unnecessary re-rendering of components, it seems prudent to extract the app state out from components and into a global store. The store should be "reactive", i.e. notify components of its updates. There are various state management libraries that do so; but since one of the goals here is to avoid additional dependencies, we will build bespoke state stores from scratch.

There are several approaches to building such a store. One is a simple pub-sub store, for example one that is based on the `EventTarget` class:

```js
class Store extends EventTarget {
  #state;

  constructor(initialState) {
    super();
    this.#state = initialState;
  }

  get state() {
    return this.#state;
  }

  update(updater) {
    this.#state = updater(this.#state);
    this.dispatchEvent(
      new CustomEvent("change", { detail: this.#state })
    );
  }

  subscribe(listener) {
    const onChange = (event) => listener(event.detail);
    this.addEventListener("change", onChange);
    listener(this.#state);
    return () => this.removeEventListener("change", onChange);
  }
}
```

A modification of this approach is the one that allows the consumer to react only to the changes of the relevant parts of the state:

```js
  class ConfigStore {
    private subscriptions = new Set<(state: ConfigState) => void>();

    getState() {
      return this.state;
    }

    subscribe(listener: (state: ConfigState) => void) {
      this.subscriptions.add(listener);
      listener(this.state);

      return () => this.subscriptions.delete(listener);
    }

    subscribeSelector<Selected>(
      selector: (state: ConfigState) => Selected,
      listener: (selected: Selected) => void,
      equality: (previous: Selected, next: Selected) => boolean = Object.is
    ) {
      let previous = selector(this.state);

      listener(previous);

      return this.subscribe((state) => {
        const next = selector(state);

        if (equality(previous, next)) {
          return;
        }

        previous = next;
        listener(next);
      });
    }
  }
```


Another approach is to base the store on a javascript `Proxy` object:

```ts
export type StoreChange =
  | {
      type: "set";
      target: object;
      key: PropertyKey;
      previousValue: unknown;
      value: unknown;
    }
  | {
      type: "delete";
      target: object;
      key: PropertyKey;
      previousValue: unknown;
      value: undefined;
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

    const objectValue = value as object;
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
            type: "set",
            target,
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
            type: "delete",
            target,
            key,
            previousValue,
            value: undefined,
          });
        }

        return deleted;
      },
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
```