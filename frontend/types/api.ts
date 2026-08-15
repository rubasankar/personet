// Shared FastAPI response types

export interface FastAPIValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}
