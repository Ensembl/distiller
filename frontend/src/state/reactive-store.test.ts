import { expect, test, describe } from 'vitest'

import { createStore, type StoreChange } from './reactive-store';

describe('proxy-based store', () => {

  const createTestStore = () => {
    const store = createStore<{
      foo: string | null;
      bar: {
        baz: number;
      };
      quox: number[];
    }>({
      foo: null,
      bar: { baz: 0 },
      quox: []
    });

    const actions = {
      incrementBar(): void {
        store.state.bar.baz++;
      },

      setFoo(name: string): void {
        store.state.foo = name;
      },

      addItem(item: number):void {
        store.state.quox.push(item);
      },

      reset(): void {
        store.state.foo = null;
        store.state.bar.baz = 0;
        store.state.quox = [];
      },
    };

    return {
      ...store,
      actions,
    };

  };


  test('detecting a change in a top-level field', () => {
    const store = createTestStore();
    let updated = false;
    const listener = (change: StoreChange) => {
      if (change.key === 'foo') {
        updated = true;
      }
    };

    store.subscribe(listener);
    store.actions.setFoo('something new');

    expect(updated).toBe(true); // the listener has fired
    expect(store.state.foo).toBe('something new'); // the state has been updated
  });


  test('detecting a change of a nested field', () => {
    const store = createTestStore();
    let updated = false;
    const listener = (change: StoreChange) => {
      if (change.target === store.state.bar && change.key === 'baz') {
        updated = true;
      }
    };

    store.subscribe(listener);
    expect(store.state.bar.baz).toBe(0); // initial state
    store.actions.incrementBar();

    expect(updated).toBe(true); // the listener has fired
    expect(store.state.bar.baz).toBe(1); // the state has been updated
  });

  test('detecting update of an array', () => {
    const store = createTestStore();
    let updated = false;
    const listener = (change: StoreChange) => {
      if (change.target === store.state.quox) {
        updated = true;
      }
    };

    store.subscribe(listener);
    expect(store.state.quox).toEqual([]); // initial state
    store.actions.addItem(42);

    expect(updated).toBe(true); // the listener has fired
    expect(store.state.quox).toEqual([42]); // the state has been updated
  });

});