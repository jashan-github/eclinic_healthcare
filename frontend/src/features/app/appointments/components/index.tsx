import { useState, type FC } from "react";
import Completed from "./completed";
import MyOPD from "./my-opd";
import Upcoming from "../upcoming";
import { FunnelIcon, MagnifyingGlassIcon, XIcon } from "@phosphor-icons/react";
import { useDoctorAppointments } from "@/hooks/use-appointment";

const ManageOngoingAppointments: FC = () => {
  const [activeTab, setActiveTab] = useState("my-opd");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortAsc, setSortAsc] = useState<boolean | null>(null);
  const [consultType] = useState<"online" | "offline" | null>();

  // Pagination state for each tab
  const [todayPage, setTodayPage] = useState(1);
  const [upcomingPage, setUpcomingPage] = useState(1);
  const [completedPage, setCompletedPage] = useState(1);
  const perPage = 20;

  // Fetch appointments with pagination for all tabs
  const {
    data: apiData,
    isLoading,
    error,
  } = useDoctorAppointments({
    today_page: todayPage,
    upcoming_page: upcomingPage,
    completed_page: completedPage,
    per_page: perPage,
  });

  // Reset page to 1 when switching tabs
  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    if (tab === "my-opd") {
      setTodayPage(1);
    } else if (tab === "upcoming") {
      setUpcomingPage(1);
    } else {
      setCompletedPage(1);
    }
  };

  // LOADING & ERROR
  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-[#F4F6F9]">
        <div className="text-gray-600">Loading appointments...</div>
      </div>
    );
  }

  if (error || !apiData) {
    return (
      <div className="h-full flex items-center justify-center bg-[#F4F6F9]">
        <div className="text-red-600">Failed to load appointments</div>
      </div>
    );
  }

  // Handle page change
  const handlePageChange = (page: number) => {
    if (activeTab === "my-opd") {
      setTodayPage(page);
    } else if (activeTab === "upcoming") {
      setUpcomingPage(page);
    } else {
      setCompletedPage(page);
    }
  };

  const tabs = [
    {
      label: `Today (${apiData.today.total || 0})`,
      value: "my-opd",
      component: (
        <MyOPD
          appointments={apiData.today.data || []}
          searchTerm={searchTerm}
          sortAsc={sortAsc}
          consultationFilter={consultType}
          pagination={apiData.today}
          currentPage={todayPage}
          onPageChange={handlePageChange}
        />
      ),
    },
    {
      label: `Upcoming (${apiData.upcoming.total || 0})`,
      value: "upcoming",
      component: (
        <Upcoming
          appointments={apiData.upcoming.data || []}
          searchTerm={searchTerm}
          sortAsc={sortAsc}
          consultationFilter={consultType}
          pagination={apiData.upcoming}
          currentPage={upcomingPage}
          onPageChange={handlePageChange}
        />
      ),
    },
    {
      label: `Completed (${apiData.completed.total || 0})`,
      value: "completed",
      component: (
        <Completed
          appointments={apiData.completed.data || []}
          searchTerm={searchTerm}
          sortAsc={sortAsc}
          consultationFilter={consultType}
          pagination={apiData.completed}
          currentPage={completedPage}
          onPageChange={handlePageChange}
        />
      ),
    },
  ];

  return (
    <div className="h-full flex flex-col rounded-lg border border-gray-300 overflow-auto">
      {/* Header */}
      <div className="bg-[#002FD4] p-1.5 flex items-center">
        {tabs.map(({ label, value }) => (
          <button
            key={value}
            onClick={() => handleTabChange(value)}
            className={`px-2 py-2 rounded-md transition-all hover:cursor-pointer 
              ${activeTab === value ? "text-white" : "text-gray-400"}`}
          >
            <div className="font-poppins text-[13px] leading-5 font-bold">
              {label}
            </div>
          </button>
        ))}

        <div className="ml-auto flex items-center">
          {isSearchOpen ? (
            <div className="flex items-center bg-white/20 rounded-md">
              <input
                type="text"
                placeholder="Search..."
                autoFocus
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-48 px-3 py-1.5 text-sm bg-transparent text-white placeholder-white/70 outline-none"
              />
              <button
                onClick={() => {
                  setSearchTerm("");
                  setIsSearchOpen(false);
                }}
                className="p-1.5 text-white hover:bg-white/20 rounded-md"
              >
                <XIcon size={18} weight="bold" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsSearchOpen(true)}
              className="p-2 text-white hover:bg-white/10 rounded-md"
            >
              <MagnifyingGlassIcon size={20} />
            </button>
          )}

          <button
            onClick={() =>
              setSortAsc((prev) =>
                prev === null ? true : prev === true ? false : null,
              )
            }
            className="text-white hover:bg-white/10 p-2 rounded-md"
          >
            <FunnelIcon
              size={20}
              weight={sortAsc !== null ? "fill" : "regular"}
            />
          </button>

          {/* 3 dots menu - same as yours */}
          {/* <div className="relative">
            <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="text-white hover:bg-white/10 p-2 rounded-md">
              <DotsThreeVerticalIcon size={20} weight="regular" />
            </button>
            {isMenuOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setIsMenuOpen(false)} />

                <div className="absolute right-0 top-10 w-64 bg-white rounded-lg shadow-2xl z-50 text-left overflow-hidden">

                  <button className="w-full px-3 py-2 flex items-center">
                    <span className="font-poppins text-[13px] leading-5 text-black capitalize">Patient History</span>
                  </button>
                </div>
              </>
            )}
          </div> */}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-4 bg-[#F4F6F9]">
        {tabs.find((tab) => tab.value === activeTab)?.component}
      </div>
    </div>
  );
};

export default ManageOngoingAppointments;
