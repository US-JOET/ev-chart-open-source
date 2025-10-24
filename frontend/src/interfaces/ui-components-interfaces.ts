export interface SortState<T> {
  column: keyof T;
  direction: string;
}

export interface OptionsList {
  value: string;
  label: string;
}
