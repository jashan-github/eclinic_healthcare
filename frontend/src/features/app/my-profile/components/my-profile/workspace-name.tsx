import { useMyProfile } from '../../hooks/use-my-profile';

export default function WorkspaceName() {

  const { myProfile } = useMyProfile();

  return (
    <div className="min- h-[128px] p-[17px] pl-[30px] rounded-[16px] border border-[#D6D9E0] bg-white flex flex-cols">
      <img 
        src={`${myProfile?.active_clinic?.logo}`}
        className='w-[92px] h-[71px] rounded-[4px] opacity-100'
      />
      <div className='my-auto ml-10 font-poppins font-bold text-[13px] leading-[20px] tracking-[1px] text-[#0F1011] align-middle'>
        {`${myProfile?.active_clinic?.name}`}
      </div>
    </div>
  );
}
