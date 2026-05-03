import ToggleCell from "@/components/ui/Toggle";
import {
  useAdminWaverNotificationSettings,
  useUpdateWaiverSettings,
} from "@/hooks/use-admin-settings";
import { useEffect, useState, type FC, type ReactElement } from "react";

type WaiverSettings = {
  waiver_enabled: boolean;
  waiver_percent: number;
  waiver_doctor_decides: boolean;
};

const AdminWaiverSettingsPage: FC = (): ReactElement => {
  const { data, isLoading } = useAdminWaverNotificationSettings();
  const { mutate, isPending } = useUpdateWaiverSettings();
  const [initialSettings, setInitialSettings] = useState<WaiverSettings | null>(
    null,
  );

  const [settings, setSettings] = useState<WaiverSettings>({
    waiver_enabled: false,
    waiver_percent: 0,
    waiver_doctor_decides: false,
  });

  useEffect(() => {
    if (!data?.data) return;

    const fetched = {
      waiver_enabled: data.data.waiver_enabled,
      waiver_percent: data.data.waiver_percent,
      waiver_doctor_decides: data.data.waiver_doctor_decides ?? false,
    };

    setSettings(fetched);
    setInitialSettings(fetched);
  }, [data]);

  const hasChanges =
    initialSettings &&
    (initialSettings.waiver_enabled !== settings.waiver_enabled ||
      initialSettings.waiver_percent !== settings.waiver_percent ||
      initialSettings.waiver_doctor_decides !== settings.waiver_doctor_decides);

  const toggleWaiver = () => {
    setSettings((prev) => ({
      waiver_enabled: !prev.waiver_enabled,
      waiver_percent: !prev.waiver_enabled ? prev.waiver_percent : 0,
      waiver_doctor_decides: !prev.waiver_enabled ? prev.waiver_doctor_decides : false,
    }));
  };

  const handleSave = () => {
    mutate({
      waiver_enabled: settings.waiver_enabled,
      waiver_percent: settings.waiver_enabled ? settings.waiver_percent : 0,
      waiver_doctor_decides: settings.waiver_doctor_decides,
    });
  };

  if (isLoading) return <>Loading</>;

  return (
    <div className="p-6">
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5E7EB]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="font-poppins font-semibold text-xl leading-6 text-[#0F1011]">
              Waiver Settings
            </h1>
            <p className="font-poppins text-sm leading-5 text-[#64748B]">
              Configure waiver preferences.
            </p>
          </div>

          <button
            onClick={handleSave}
            disabled={!hasChanges || isPending}
            className="px-5 py-2 rounded-lg bg-[#002FD4] text-white text-sm disabled:opacity-60"
          >
            {isPending ? "Saving..." : "Save Changes"}
          </button>
        </div>
        <div className="overflow-x-auto">
          <div className="min-w-[800px] border border-[#E4E5ED] rounded-lg overflow-hidden">
            <table className="w-full table-auto border-collapse">
              <thead className="bg-[#E8EEFD]">
                <tr>
                  <th className="py-4 px-6 font-poppins font-bold text-[12px] text-left text-[#0F1011]">
                    Waiver
                  </th>
                  <th className="py-4 px-6 font-poppins font-bold text-[12px] text-center text-[#0F1011]">
                    Enabled
                  </th>
                </tr>
              </thead>

              <tbody className="bg-white divide-y divide-[#E4E5ED]">
                <tr className="hover:bg-[#F9FAFB] transition-colors">
                  <td className="py-5 px-6 first:pl-8">
                    <span className="font-poppins font-medium text-[13px] text-[#0F1011]">
                      Service fee waiver
                    </span>
                  </td>

                  <ToggleCell
                    value={settings.waiver_enabled}
                    onClick={toggleWaiver}
                  />
                </tr>

                {settings.waiver_enabled && (
                  <tr className="hover:bg-[#F9FAFB] transition-colors">
                    <td className="py-5 px-6 first:pl-8">
                      <span className="font-poppins font-medium text-[13px] text-[#0F1011]">
                        Doctor decides waiver per request
                      </span>
                    </td>

                    <ToggleCell
                      value={settings.waiver_doctor_decides}
                      onClick={() =>
                        setSettings((prev) => ({
                          ...prev,
                          waiver_doctor_decides: !prev.waiver_doctor_decides,
                        }))
                      }
                    />
                  </tr>
                )}

                {settings.waiver_enabled && !settings.waiver_doctor_decides && (
                  <tr className="hover:bg-[#F9FAFB] transition-colors">
                    <td className="py-5 px-6 first:pl-8">
                      <span className="font-poppins font-medium text-[13px] text-[#0F1011]">
                        Waiver percentage
                      </span>
                    </td>

                    <td className="py-5 px-6">
                      <div className="flex items-center gap-4 justify-center">
                        <span className="min-w-[48px] text-right font-poppins text-sm text-[#0F1011]">
                          {settings.waiver_percent}%
                        </span>

                        <input
                          type="range"
                          min={0}
                          max={100}
                          value={settings.waiver_percent}
                          onChange={(e) =>
                            setSettings((prev) => ({
                              ...prev,
                              waiver_percent: Number(e.target.value),
                            }))
                          }
                          className="w-40"
                        />
                      </div>
                    </td>
                  </tr>
                )}

                {settings.waiver_enabled && settings.waiver_doctor_decides && (
                  <tr className="hover:bg-[#F9FAFB] transition-colors">
                    <td colSpan={2} className="py-4 px-6 first:pl-8">
                      <span className="font-poppins text-sm text-[#64748B] italic">
                        Doctor sets waiver when accepting each request
                      </span>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminWaiverSettingsPage;
