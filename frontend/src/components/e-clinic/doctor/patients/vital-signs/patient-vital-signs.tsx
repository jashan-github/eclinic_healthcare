// patient-vital-signs.tsx
const historicalData = [
    { date: '2025-01-14', weightLbs: 233.2, weightKg: 105.8, heightIn: 72.0, heightCm: 182.9, bpSystolic: 110, bpDiastolic: 80 },
    { date: '2024-10-01', weightLbs: 195.5, weightKg: 84.1, heightIn: 72.0, heightCm: 182.9, bpSystolic: 110, bpDiastolic: 80 },
    { date: '2024-08-26', weightLbs: 182.0, weightKg: 82.6, heightIn: 72.0, heightCm: 182.9, bpSystolic: 110, bpDiastolic: 70 },
    { date: '2024-05-30', weightLbs: 188.2, weightKg: 85.4, heightIn: 72.0, heightCm: 182.9, bpSystolic: 100, bpDiastolic: 70 },
    { date: '2024-02-16', weightLbs: 180.1, weightKg: 81.7, heightIn: 72.0, heightCm: 182.9, bpSystolic: 110, bpDiastolic: 80 },
    { date: '2023-12-01', heightIn: 210.48, heightCm: 210.48 },
    { date: '2023-10-01', heightIn: 230.44, heightCm: 230.44, bpSystolic: 120, bpDiastolic: 80 },
];

const currentVitals = {
    weightLbs: 188.5, weightKg: 84.1, heightIn: 72.0, heightCm: 182.9,
    bpSystolic: 118, bpDiastolic: 76, pulse: 72, respiration: 16, tempF: 98.6, tempC: 37.0,
};

const rows = [
    { name: 'Weight', unit: 'lbs', current: currentVitals.weightLbs, key: 'weightLbs' },
    { name: 'Weight', unit: 'kg', current: currentVitals.weightKg, key: 'weightKg' },
    { name: 'Height/Length', unit: 'in', current: currentVitals.heightIn, key: 'heightIn' },
    { name: 'Height/Length', unit: 'cm', current: currentVitals.heightCm, key: 'heightCm' },
    { name: 'BP Systolic', unit: 'mmHg', current: currentVitals.bpSystolic, key: 'bpSystolic' },
    { name: 'BP Diastolic', unit: 'mmHg', current: currentVitals.bpDiastolic, key: 'bpDiastolic' },
    { name: 'Pulse', unit: 'per min', current: currentVitals.pulse },
    { name: 'Respiration', unit: 'per min', current: currentVitals.respiration },
    { name: 'Temperature', unit: '°F', current: currentVitals.tempF },
    { name: 'Temperature', unit: '°C', current: currentVitals.tempC },
    { name: 'Temp Location', unit: '', current: '' },
    { name: 'Blood Sugar', unit: 'mg/dl', current: '' },
    { name: 'Oxygen Saturation', unit: '%', current: '' },
    { name: 'Head Circumference', unit: 'in', current: '' },
    { name: 'Head Circumference', unit: 'cm', current: '' },
    { name: 'Waist Circumference', unit: 'in', current: '' },
    { name: 'Waist Circumference', unit: 'cm', current: '' },
    { name: 'BMI', unit: 'kg/m²', current: '' },
    { name: 'BMI Status', unit: 'Type', current: '' },
    { name: 'Other Notes', unit: '', current: '' },
];

const formatDate = (d: string) =>
    new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: '2-digit' }).replace(/\//g, '-');

export default function VitalsTable() {
  return (
    <div className="w-full bg-white rounded-lg shadow-lg overflow-hidden text-sm font-sans">
      <div className="flex">
        {/* ==================== TABLE 1: Fixed Left (Name + Unit + Current) ==================== */}
        <div className="flex-none border-r border-gray-300 rounded-lg shadow-lg">
          {/* Header */}
          <div className="flex border-b-2 border-gray-300 h-[66px]">
            <div className="px-6 pt-6 font-semibold text-gray-800 text-left w-48">Name</div>
            <div className="px-6 pt-6 font-semibold text-gray-800 text-center w-24">Unit</div>
            <div className="px-6 pt-6 font-bold text-gray-900 text-center w-32 border-r border-gray-400 rounded-tr-lg">
              Current
            </div>
          </div>

          {/* Body */}
          <div>
            {rows.map((row, idx) => (
                
              <div
                key={idx}
                className="flex border-b border-gray-200 hover:bg-gray-50/30 transition-colors h-12"
              >
                <div className="w-48 px-6 flex items-center justify-start font-medium text-gray-800 sticky left-0 bg-white z-10">
                  {row.name}
                </div>
                <div className="w-24 flex items-center justify-center text-gray-600">
                  {row.unit || '-'}
                </div>
                <div className="w-32 flex items-center justify-center font-bold text-gray-900 bg-white border-r border-gray-400">
                  {row.current || '-'}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ==================== TABLE 2: Scrollable Historical Data ==================== */}
        <div className="flex-1 overflow-x-auto">
          {/* Header */}
          <div className="flex border-b-2 border-gray-300">
            {historicalData.map((entry) => (
              <div
                key={entry.date}
                className="w-[110px] min-w-[110px] flex items-center justify-center text-center font-medium text-gray-700 border-l border-gray-200 h-16"
              >
                {formatDate(entry.date)}
              </div>
            ))}
          </div>

          {/* Body */}
          <div>
            {rows.map((row, idx) => (
              <div
                key={idx}
                className="flex border-b border-gray-200 hover:bg-gray-50/30 transition-colors h-12"
              >
                {historicalData.map((entry, i) => {
                  const value = row.key ? (entry as any)[row.key] : undefined;
                  const display =
                    value !== undefined && value !== null
                      ? Number.isInteger(value)
                        ? value
                        : Number(value).toFixed(1)
                      : '-';

                  return (
                    <div
                      key={i}
                      className="w-[110px] min-w-[110px] flex items-center justify-center text-center text-gray-700 border-l border-gray-200 first:border-l-0"
                    >
                      {display}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
