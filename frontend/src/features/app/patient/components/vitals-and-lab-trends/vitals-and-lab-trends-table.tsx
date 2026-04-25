import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import {
  usePatientVitalSigns,
  useSaveVitalSigns,
  useVitalNames,
} from '@/components/e-clinic/patient/hook/use-vital-signs';
import React from 'react';
import { FloppyDiskIcon, NotePencilIcon } from '@phosphor-icons/react';
import VitalSignsTable from '@/components/e-clinic/patient/vital-signs/vital-signs-table';

interface VitalsAndLabTrendsTableProps {
  patientId: string;
}

// Utility to normalize name for matching
const normalizeName = (name: string) =>
  name
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[^a-z0-9()]/g, '');

// Find paired vital dynamically
const findPairedVital = (currentVital: any, allVitals: any[]) => {
  const currentNorm = normalizeName(currentVital.name);

  const pairPatterns = [
    // Weight
    { pattern: 'weight(kg)', pairPattern: 'weight(lbs)', direction: 'kg_to_lbs' },
    { pattern: 'weight(lbs)', pairPattern: 'weight(kg)', direction: 'lbs_to_kg' },
    // Height
    { pattern: 'height(cm)', pairPattern: 'height(in)', direction: 'cm_to_in' },
    { pattern: 'height(in)', pairPattern: 'height(cm)', direction: 'in_to_cm' },
    // Temperature
    { pattern: 'temperature(f)', pairPattern: 'temperature(c)', direction: 'f_to_c' },
    { pattern: 'temperature(c)', pairPattern: 'temperature(f)', direction: 'c_to_f' },
    // Head Circumference
    { pattern: 'headcircumference(in)', pairPattern: 'headcircumference(cm)', direction: 'in_to_cm' },
    { pattern: 'headcircumference(cm)', pairPattern: 'headcircumference(in)', direction: 'cm_to_in' },
    // Waist Circumference
    { pattern: 'waistcircumference(in)', pairPattern: 'waistcircumference(cm)', direction: 'in_to_cm' },
    { pattern: 'waistcircumference(cm)', pairPattern: 'waistcircumference(in)', direction: 'cm_to_in' },
  ];

  const match = pairPatterns.find((p) => currentNorm.includes(p.pattern));
  if (!match) return null;

  const pair = allVitals.find((v) =>
    normalizeName(v.name).includes(match.pairPattern)
  );

  if (!pair) return null;

  return {
    pairedVital: pair,
    direction: match.direction,
  };
};

const convertValue = (value: number, direction: string): number => {
  switch (direction) {
    case 'kg_to_lbs': return value * 2.20462;
    case 'lbs_to_kg': return value / 2.20462;
    case 'cm_to_in': return value / 2.54;
    case 'in_to_cm': return value * 2.54;
    case 'f_to_c': return (value - 32) * 5 / 9;
    case 'c_to_f': return value * 9 / 5 + 32;
    default: return value;
  }
};

const VitalsAndLabTrendsTable = ({ patientId }: VitalsAndLabTrendsTableProps) => {
  const [isEditMode, setIsEditMode] = useState(false);

  const { data: vitalNames = [], isLoading: namesLoading } = useVitalNames();
  const { data: vitalsResponse, isLoading: vitalsLoading } = usePatientVitalSigns(patientId);
  const saveMutation = useSaveVitalSigns();

  const currentVitals = React.useMemo<Record<string, string | number>>(() => {
    if (!vitalsResponse?.vital_signs) return {};
    const map: Record<string, string | number> = {};
    vitalsResponse.vital_signs.forEach((record) => {
      const value = record.numeric_value ?? record.text_value ?? '';
      map[record.vital_name_id] = value;
    });
    return map;
  }, [vitalsResponse]);

  const [editableVitals, setEditableVitals] = useState<Record<string, string | number>>(currentVitals);
  const [originalVitals] = useState<Record<string, string | number>>({});

  // Track which fields were empty when edit mode started
  // const initiallyEmptyRef = useRef<Record<string, boolean>>({});

  useEffect(() => {
    setEditableVitals(currentVitals);
  }, [currentVitals]);

  // useEffect(() => {
  //   if (isEditMode) {
  //     setOriginalVitals(currentVitals);
  //     setEditableVitals(currentVitals);

  //     const map: Record<string, boolean> = {};
  //     vitalNames.forEach((vital) => {
  //       const value = currentVitals[vital.id];
  //       map[vital.id] = value === '' || value === null || value === undefined;
  //     });
  //     initiallyEmptyRef.current = map;
  //   }
  // }, [isEditMode, currentVitals, vitalNames]);

  const handleCurrentChange = (vitalNameId: string, rawValue: string) => {
    const vital = vitalNames.find((v) => v.id === vitalNameId);
    if (!vital) return;

    let value: string | number = rawValue.trim();

    if (vital.data_type === 'number') {
      const num = rawValue === '' ? '' : parseFloat(rawValue);
      value = isNaN(num as any) ? '' : num;
    }

    setEditableVitals((prev) => ({
      ...prev,
      [vitalNameId]: value,
    }));

    // Handle paired field
    if (vital.data_type !== 'number' || typeof value !== 'number' || isNaN(value)) {
      const pairInfo = findPairedVital(vital, vitalNames);
      if (pairInfo) {
        setEditableVitals((prev) => ({
          ...prev,
          [pairInfo.pairedVital.id]: '',
        }));
      }
      handleBMICalculation();
      return;
    }

    // Valid number → update paired
    const pairInfo = findPairedVital(vital, vitalNames);
    if (pairInfo) {
      const converted = Math.round(convertValue(value, pairInfo.direction) * 10) / 10;
      setEditableVitals((prev) => ({
        ...prev,
        [pairInfo.pairedVital.id]: converted,
      }));
    }

    // Trigger BMI recalc if weight/height changed
    if (
      vital.name.toLowerCase().includes('weight') ||
      vital.name.toLowerCase().includes('height')
    ) {
      handleBMICalculation();
    }
  };

  const handleBMICalculation = () => {
    const bmiVital = vitalNames.find((v) => normalizeName(v.name).includes('bmi'));
    if (!bmiVital) return;

    // Get weight in kg
    const weightKgVital = vitalNames.find((v) => normalizeName(v.name).includes('weight(kg)'));
    let weightKg = weightKgVital ? editableVitals[weightKgVital.id] : '';

    if (typeof weightKg !== 'number' || isNaN(weightKg as any)) {
      const weightLbsVital = vitalNames.find((v) => normalizeName(v.name).includes('weight(lbs)'));
      const lbs = weightLbsVital ? editableVitals[weightLbsVital.id] : '';
      weightKg =
        typeof lbs === 'number' && !isNaN(lbs as any)
          ? Math.round((lbs as number / 2.20462) * 10) / 10
          : '';
    }

    // Get height in cm
    const heightCmVital = vitalNames.find((v) => normalizeName(v.name).includes('height(cm)'));
    let heightCm = heightCmVital ? editableVitals[heightCmVital.id] : '';

    if (typeof heightCm !== 'number' || isNaN(heightCm as any)) {
      const heightInVital = vitalNames.find((v) => normalizeName(v.name).includes('height(in)'));
      const inches = heightInVital ? editableVitals[heightInVital.id] : '';
      heightCm =
        typeof inches === 'number' && !isNaN(inches as any)
          ? Math.round((inches as number * 2.54) * 10) / 10
          : '';
    }

    if (
      typeof weightKg === 'number' &&
      typeof heightCm === 'number' &&
      heightCm > 0
    ) {
      const heightM = heightCm / 100;
      const bmi = weightKg / (heightM * heightM);
      const rounded = Math.round(bmi * 10) / 10;
      setEditableVitals((prev) => ({
        ...prev,
        [bmiVital.id]: rounded,
      }));
    } else {
      setEditableVitals((prev) => ({
        ...prev,
        [bmiVital.id]: '',
      }));
    }
  };

  const handleSave = () => {
    const changedVitals = vitalNames
      .map((vital) => {
        const oldValue = originalVitals[vital.id];
        const newValue = editableVitals[vital.id];
        if (String(oldValue ?? '') !== String(newValue ?? '')) {
          return {
            vital_name_id: vital.id,
            value: newValue ?? '',
          };
        }
        return null;
      })
      .filter(Boolean) as { vital_name_id: string; value: string | number }[];

    if (changedVitals.length === 0) {
      setIsEditMode(false);
      return;
    }

    saveMutation.mutate(
      {
        vitals: changedVitals,
        patientId: patientId,
      },
      {
        onSuccess: () => {
          setIsEditMode(false);
          toast.success('Vital signs updated successfully');
        },
        onError: (error) => {
          console.error('Save failed:', error);
          toast.error('Failed to save changes');
        },
      }
    );
  };

  const handleEditData = () => {
    if (isEditMode) {
      handleSave();
    } else {
      setIsEditMode(true);
    }
  };

  if (namesLoading || vitalsLoading) {
    return (
      <div className="p-6 text-center text-gray-600 text-lg">
        Loading vital signs...
      </div>
    );
  }

  return (
    <div className="h-screen overflow-y-auto bg-[#F4F6F9]">
      <div className="p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="font-poppins font-bold text-[20px] leading-[28px] text-[#0F1011] mb-1">
              Recorded Vitals
            </h2>
            <p className="font-poppins font-normal text-[14px] leading-[20px] text-[#64748B] mb-4">
              Update and manage patient vital signs
            </p>
          </div>
          <button
            onClick={handleEditData}
            disabled={saveMutation.isPending}
            className="px-4 py-1.5 bg-transparent hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed 
                     text-[#002FD4] font-poppins font-semibold text-sm leading-5 
                     rounded-md transition-all flex items-center gap-2 
                     border border-[#002FD4] hover:border-[#001FB8]"
          >
            {saveMutation.isPending ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-[#002FD4] border-t-transparent" />
                Saving...
              </>
            ) : isEditMode ? (
              <>
                <FloppyDiskIcon size={18} weight="bold" />
                Save Data
              </>
            ) : (
              <>
                <NotePencilIcon size={18} weight="bold" />
                Edit Data
              </>
            )}
          </button>
        </div>

        {/* Table */}
        <div className="mb-6">
          <VitalSignsTable
            isEditMode={isEditMode}
            vitalNames={vitalNames}
            currentVitals={isEditMode ? editableVitals : currentVitals}
            onCurrentChange={handleCurrentChange}
          />
        </div>
      </div>
    </div>
  );
};

export default VitalsAndLabTrendsTable;