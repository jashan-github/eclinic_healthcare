import { type FC, type ReactElement } from "react";
import { SingleCard } from "./single-card";
import { useGetCommissionsStats } from "@/hooks/use-admin-comission-rate";

type CommissionStats = {
  total_commissions_this_month: number;
  total_commission_rates: number;
  average_commission: number;
  month: number;
  year: number;
};

const CommissionCards: FC = (): ReactElement => {
  const { data, isLoading } = useGetCommissionsStats();

  const stats: CommissionStats | undefined = data?.data;

  if (!stats) return <div>No data</div>;
  if (isLoading) return <div>NO data</div>;
  const cards = [
    {
      title: "Total Commissions (This Month)",
      value: stats.total_commissions_this_month,
      prefix: "XCG",
    },

    {
      title: "Average Commission",
      value: stats.average_commission,
      suffix: "%",
    },
    {
      title: "Total Commission Rates",
      value: stats.total_commission_rates,
    },
  ];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <SingleCard
          key={card.title}
          title={card.title}
          value={card.value}
          prefix={card.prefix}
          suffix={card.suffix}
        />
      ))}
    </div>
  );
};

export default CommissionCards;
