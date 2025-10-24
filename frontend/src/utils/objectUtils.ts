export function setEveryValueInObject<T extends string, K>(obj: Record<T, K>, value: K): Record<T, K> {
  const newObject = obj;
  Object.keys(newObject).forEach((key) => {
    newObject[key as T] = value;
  });
  return newObject;
}
