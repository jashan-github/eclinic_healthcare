import { type FC, type ReactElement } from "react";

const AuthHero: FC = (): ReactElement => {
  return (
    <h1 className="text-center font-semibold text-3xl md:text-4xl leading-tight md:leading-normal tracking-normal capitalize">
      <span>Your </span>
      <span className="italic text-primary">Digital Healthcare </span>
      <span>Companion</span>
    </h1>
  );
};

export default AuthHero;
