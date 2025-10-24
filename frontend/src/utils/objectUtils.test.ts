import { expect, test } from "vitest";
import { setEveryValueInObject } from "./objectUtils";

test("setEveryValueInObject 0", () => {
  const obj = { a: 123, b: 4 };
  expect(setEveryValueInObject(obj, 0)).toStrictEqual({ a: 0, b: 0 });
});
