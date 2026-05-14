// vital-signs-table.tsx
import React from 'react';
import { format } from 'date-fns';
import type { VitalName } from '../service/vital-signs-service';
import { usePatientVitalHistory } from '@/components/e-clinic/patient/hook/use-vital-signs';
import { useAuth } from '@/context/auth/auth-context-utils';
import { useParams } from '@tanstack/react-router';

interface Props {
  isEditMode: boolean;
  vitalNames: VitalName[];
  currentVitals: Record<string, string | number>;
  onCurrentChange: (vitalNameId: string, value: string) => void;
}

const formatDate = (dateStr: string) =>
  format(new Date(dateStr), 'MM/dd/yyyy');

export default function VitalSignsTable({
  isEditMode,
  vitalNames,
  currentVitals,
  onCurrentChange,
}: Props) {
  const { user } = useAuth();
  let patientId = '';
  const urlId = useParams({ strict: false })
  if(user?.role === 'patient'){
    patientId = user.id
  }
  else{
    patientId = urlId.patientId
  }

  const {
    data: historyResponse,
    isLoading: historyLoading,
    isError: historyError,
  } = usePatientVitalHistory(patientId!);
    // const editableOnStart = React.useRef<Record<string, boolean>>({});

  // Process history – now handles ARRAY structure correctly
  const { historicalDates, getValueForDateAndVital } = React.useMemo(() => {
    if (!historyResponse?.vital_signs_by_date) {
      return {
        historicalDates: [],
        getValueForDateAndVital: () => '-',
      };
    }

    const data = historyResponse.vital_signs_by_date;
    const dates = Object.keys(data).sort((a, b) => b.localeCompare(a)); // newest first

    // Build lookup: date → vital_name_id → value
    const valueMap = new Map<string, string | number>();

    dates.forEach((date) => {
      const entries = data[date];
      entries.forEach((entry: any) => {
        if (entry.id !== null) {
          const value = entry.numeric_value ?? entry.text_value ?? '';
          valueMap.set(`${date}|||${entry.vital_name_id}`, value);
        }
      });
    });

    const getValue = (date: string, vitalId: string): string => {
      const raw = valueMap.get(`${date}|||${vitalId}`);
      if (raw === undefined || raw === '' || raw === null) return '-';

      if (typeof raw === 'number') {
        return Number.isInteger(raw) ? raw.toString() : raw.toFixed(1);
      }
      return raw.toString();
    };

    return { historicalDates: dates, getValueForDateAndVital: getValue };
  }, [historyResponse]);
// const initialVitalsRef = React.useRef<Record<string, string | number>>({});

// useEffect(() => {
//   if (isEditMode) {
//     initialVitalsRef.current = { ...currentVitals };

//     const map: Record<string, boolean> = {};

//     vitalNames.forEach((vital) => {
//       const value = initialVitalsRef.current[vital.id];
//       map[vital.id] = value === '' || value === null || value === undefined;
//     });

//     editableOnStart.current = map;
//   }
// }, [isEditMode, vitalNames]);


  if (vitalNames.length === 0) {
    return <div className="text-center py-8 text-gray-500">Loading vital signs...</div>;
  }

  if (historyLoading) {
    return <div className="text-center py-8 text-gray-500">Loading history...</div>;
  }

  if (historyError) {
    return <div className="text-center py-8 text-red-500">Failed to load history</div>;
  }

  return (
    <div className="w-full bg-white rounded-lg shadow-lg overflow-hidden text-sm font-sans">
      <div className="flex">
        {/* Fixed Left Column */}
        <div className="flex-none border-r border-gray-300">
          {/* Header */}
          <div className="flex border-b-2 border-gray-300 h-[66px]">
            <div className="px-6 pt-6 font-poppins font-semibold text-base leading-6 text-[#002FD4] text-left w-64">Name</div>
            <div className="px-6 pt-6 font-poppins font-semibold text-base leading-6 text-[#002FD4] text-center w-24">Unit</div>
            <div className="px-6 pt-6 font-poppins font-semibold text-base leading-6 text-[#002FD4] text-center w-32 border-r border-gray-400">Current</div>
          </div>

          {/* Body */}
          <div>
            {vitalNames.map((vital) => {
              const rawValue = currentVitals[vital.id] ?? '';
              // const hasValue = rawValue !== '' && rawValue !== null && rawValue !== undefined;

              const displayValue =
                rawValue === '' || rawValue === null || rawValue === undefined
                  ? '-'
                  : typeof rawValue === 'number'
                    ? Number.isInteger(rawValue)
                      ? rawValue
                      : Number(rawValue).toFixed(1)
                    : rawValue;

              // Only allow editing if NO value exists
              // const isEditable = isEditMode && editableOnStart.current[vital.id];
const isEditable = isEditMode;
              return (
                <div key={vital.id} className="flex hover:bg-gray-50/30 transition-colors h-12">
                  <div className="w-64 px-6 flex items-center justify-start font-semibold text-gray-800 sticky left-0 bg-white z-10">
                    {vital.name}
                  </div>
                  <div className="w-24 flex items-center justify-center text-gray-600">
                    {vital.unit || '-'}
                  </div>
                  <div className="w-32 flex items-center justify-center border-r border-gray-400">
                    <div className="w-28 h-8 px-3 flex items-center justify-center bg-[#F9FAFB] border border-[#E1E7EF] rounded-md">
                      {isEditable ? (
                        vital.data_type === 'select' && vital.options ? (
                          <select
                            value={rawValue as string}
                            onChange={(e) => onCurrentChange(vital.id, e.target.value)}
                            className="w-full h-full bg-transparent border-0 outline-none font-bold text-center"
                          >
                            <option value="">-</option>
                            {vital.options.map((opt) => (
                              <option key={opt} value={opt}>{opt}</option>
                            ))}
                          </select>
                        ) : vital.data_type === 'text' ? (
                          <textarea
                            value={rawValue as string}
                            onChange={(e) => onCurrentChange(vital.id, e.target.value)}
                            rows={1}
                            className="w-full h-full bg-transparent border-0 outline-none resize-none font-bold text-center"
                          />
                        ) : (
                          <input
                            type="text"
                            value={rawValue as string}
                            onChange={(e) => onCurrentChange(vital.id, e.target.value)}
                            className="w-full h-full bg-transparent border-0 outline-none font-bold text-center"
                          />
                        )
                      ) : (
                        <span className="font-bold">{displayValue}</span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Historical Columns – remains same */}
        <div className="flex-1 overflow-x-auto">
          {/* ... (same as before) */}
          <div className="flex border-b-2 border-gray-300">
            {historicalDates.length === 0 ? (
              <div className="px-6 py-4 text-gray-500 text-center w-full">No historical data</div>
            ) : (
              historicalDates.map((date) => (
                <div
                  key={date}
                  className="w-[110px] min-w-[110px] flex items-center justify-center text-center font-medium text-gray-700 border-l border-gray-200 h-16"
                >
                  {formatDate(date)}
                </div>
              ))
            )}
          </div>

          <div>
            {vitalNames.map((vital) => (
              <div key={vital.id} className="flex border-b border-gray-200 hover:bg-gray-50/30 transition-colors h-12">
                {historicalDates.length === 0 ? (
                  <div className="w-full text-center text-gray-400 py-3">-</div>
                ) : (
                  historicalDates.map((date) => (
                    <div
                      key={date}
                      className="w-[110px] min-w-[110px] flex items-center justify-center text-center text-gray-700 border-l border-gray-200 first:border-l-0"
                    >
                      {getValueForDateAndVital(date, vital.id)}
                    </div>
                  ))
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
