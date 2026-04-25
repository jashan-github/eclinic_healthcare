import { type FC, type ReactElement } from "react";
import {
  // CurrencyDollarIcon,
  // UsersIcon,
  CameraIcon,
} from "@phosphor-icons/react";
import { SingleCard } from "./single-card";
import { useDashboardStats } from "@/hooks/use-dashboard";
import { Loader } from "@mantine/core";

const FourCards: FC = (): ReactElement => {
  const { data, isLoading, isError } = useDashboardStats();

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-8">
        <Loader size="sm" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="text-center text-[#64748B] py-8">
        Failed to load dashboard stats
      </div>
    );
  }

  const cards = [
    { id: 1, title: "Total Revenue", value: data.total_revenue },
    {
      id: 2,
      title: "Total Commissions",
      value: data.total_commissions,
    },
    {
      id: 3,
      title: "Total Webinars (This month)",
      value: data.total_webinars_this_month,
      Icon: CameraIcon,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {cards.map((c) => (
        <SingleCard
          key={c.id}
          title={c.title}
          value={c.value}
          Icon={c.Icon}
          currency={data.currency}
        />
      ))}
    </div>
  );
};

export default FourCards;
