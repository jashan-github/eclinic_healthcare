import WebinarContent from "@/components/e-clinic/doctor/webinars/webinar-content";
import { ClockClockwiseIcon } from "@phosphor-icons/react";
import { type FC, type ReactElement } from "react";

const DoctorWebinar: FC = (): ReactElement => {
  return (
    <div className="bg-[#F4F6F9] w-full h-full px-6 py-8 overflow-auto">
      <div className="flex w-full justify-between items-center mb-10 gap-4 flex-wrap">
        <div className="font-poppins font-medium text-lg leading-6 text-[#0F1011]">
          Your webinars
        </div>
        <div
          role="status"
          className="flex items-center gap-2 rounded-md border border-[#E4E5ED] bg-white px-4 py-2"
        >
          <ClockClockwiseIcon size={16} weight="bold" className="text-[#002FD4]" />
          <span className="font-poppins text-sm leading-5 text-[#475569]">
            Webinar hosting is coming soon — contact your admin to schedule one.
          </span>
        </div>
      </div>
      <div>
        <WebinarContent />
      </div>
    </div>
  );
};

export default DoctorWebinar;
