import { expect, test } from "vitest";
import { validateEmail } from "./email";

test("valid email", () => {
  expect(validateEmail("ag@aol.com")).toBe(true);
});

test("invalid email", () => {
  expect(validateEmail("ag@aolom")).toBe(false);
});
