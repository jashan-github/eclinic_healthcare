import { type FC, type ReactElement } from "react";

const Welcome: FC = (): ReactElement => {
  return (
    <div className="flex w-full pt-4 justify-between items-center font-poppins">
      <div className="font-medium text-[18px] leading-6 align-middle">
        Welcome back! Here's your Clinic overview
      </div>
    </div>
  );
};

export default Welcome;
