import WebinarContent from "@/components/e-clinic/doctor/webinars/webinar-content";
import { type FC, type ReactElement } from "react";

const DoctorWebinar: FC = (): ReactElement => {
  return (
    <div className="bg-[#F4F6F9] w-full h-full px-6 py-8 overflow-auto">
      <div className="flex w-full justify-between items-center mb-10">
        <div className="font-poppins font-medium text-lg leading-6 text-[#0F1011]">
          Host and manage your webinars
        </div>
        <div>
          <button
            className="w-[166px] h-10 opacity-10 rounded-md px-[13px] py-[9px] bg-[#002FD4]"
            disabled={true}
          >
            <span className="font-poppins font-semibold text-sm leading-5 text-center text-white">
              Host a webinar
            </span>
          </button>
        </div>
      </div>
      <div>
        <WebinarContent />
      </div>
    </div>
  );
};

export default DoctorWebinar;
