import React from "react";

interface HeadSubheadProps {
  head: string;
  subhead: string;
}

const HeadSubhead: React.FC<HeadSubheadProps> = ({ head, subhead }) => {
  return (
    <div>
      <h2 className="font-poppins font-semibold text-[20px] leading-[24px] mb-1">
        {head}
      </h2>
      <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B]">
        {subhead}
      </p>
    </div>
  );
};

export default HeadSubhead;
