const ToggleCell = ({
  value,
  onClick,
}: {
  value: boolean;
  onClick: () => void;
}) => (
  <td className="py-5 px-6 text-center">
    <button
      onClick={onClick}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        value ? "bg-[#002FD4]" : "bg-gray-300"
      }`}
    >
      <span
        className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
          value ? "translate-x-5" : "translate-x-0.5"
        }`}
      />
    </button>
  </td>
);

export default ToggleCell;
