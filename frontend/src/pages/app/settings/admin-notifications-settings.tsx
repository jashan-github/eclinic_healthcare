import ToggleCell from "@/components/ui/Toggle";
import {
  useAdminNotificationSettings,
  useUpdateNotificationSettings,
} from "@/hooks/use-admin-settings";
import { useEffect, useState, type FC, type ReactElement } from "react";

type NotificationSettings = Record<string, boolean>;
type NotificationLabels = Record<string, string>;

const AdminNotificationsSettingsPage: FC = (): ReactElement => {
  const { data } = useAdminNotificationSettings();

  const [settings, setSettings] = useState<NotificationSettings>({});
  const [labels, setLabels] = useState<NotificationLabels>({});

  const { mutate, isPending } = useUpdateNotificationSettings();
  const capitalize = (str: string) =>
    str.charAt(0).toUpperCase() + str.slice(1);

  useEffect(() => {
    if (!data?.data || !data?.data?.labels) return;

    const { labels, ...rest } = data.data;

    setSettings(rest ?? {});
    setLabels(labels ?? {});
  }, [data]);

  const toggle = (key: string) => {
    setSettings((prev) =>
      prev
        ? {
            ...prev,
            [key]: !prev[key],
          }
        : prev,
    );
  };

  const handleSave = () => {
    if (!settings) return;
    mutate(settings);
  };

  if (!labels || Object.keys(labels).length === 0) {
    return (
      <div className="p-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5E7EB]">
          <div className="text-sm text-[#64748B]">Loading…</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-[#E5E7EB]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="font-poppins font-semibold text-xl leading-6 text-[#0F1011]">
              Notifications Settings
            </h1>
            <p className="font-poppins text-sm leading-5 text-[#64748B]">
              Configure notification preferences for admin users.
            </p>
          </div>

          <button
            onClick={handleSave}
            disabled={isPending}
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
                  <th className="py-4 px-6 text-left">Notification</th>
                  <th className="py-4 px-6 text-center">Enabled</th>
                </tr>
              </thead>

              <tbody>
                {!settings && !labels && <div>NO DATA</div>}
                {Object.entries(labels).map(([key, label]) => (
                  <tr
                    key={key}
                    className="hover:bg-[#F9FAFB] transition-colors"
                  >
                    {/* <td className="py-4 px-6 font-medium"></td> */}
                    <td className="py-5 px-6 first:pl-8">
                      <span className="font-poppins font-medium text-[13px] text-[#0F1011]">
                        {capitalize(label)}
                      </span>
                    </td>

                    <ToggleCell
                      value={!!settings[key]}
                      onClick={() => toggle(key)}
                    />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      {/* <p className='font-poppins text-sm leading-5 text-[#64748B] text-center mt-4'>Comming Soon...</p> */}
    </div>
  );
};

export default AdminNotificationsSettingsPage;
