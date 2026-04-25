import type { FC, ReactElement } from "react";

type SingleCardProps = {
  title: string;
  value: number | string;
  prefix?: string;
  suffix?: string;
  Icon?: any;
};

export const SingleCard: FC<SingleCardProps> = ({
  title,
  value,
  prefix,
  suffix,
  Icon,
}): ReactElement => {
  const formattedValue =
    typeof value === "number" ? value.toLocaleString("en-US") : value;

  return (
    <div className="flex justify-between items-center bg-white rounded-2xl p-4 shadow-[0_1px_2px_0_#0000000D] border border-[#E2E8F0]">
      <div className="flex flex-col">
        <span className="text-[#64748B] font-semibold text-[14px] leading-[20px]">
          {title}
        </span>
        <span className="text-[#0F1011] font-bold text-[24px] leading-[32px]">
          {prefix && `${prefix} `}
          {formattedValue}
          {suffix}
        </span>
      </div>
      {Icon ? <Icon size={20} weight="bold" color="#002FD4" /> : null}
    </div>
  );
};
