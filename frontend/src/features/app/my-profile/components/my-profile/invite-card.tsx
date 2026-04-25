import { Avatar, Text, Group } from '@mantine/core';

interface InviteCardProps {
    name: string;
    inviteCode?: string;
}

export default function InviteCard({ name }: InviteCardProps) {
    // Extract first letter (after trimming, ignore "Dr.", "Mr.", etc.)
    const getAvatarLetter = (fullName: string) => {
        const cleaned = fullName.replace(/^(Dr\.?|Mr\.?|Mrs\.?|Ms\.?)\s*/i, '').trim();
        return cleaned.charAt(0).toUpperCase();
    };

    const avatarLetter = getAvatarLetter(name);

    return (
        <div className="bg-white p-4 max-w-sm mx-auto border-b border-gray-300">
            <Group gap="md" align="center">
                {/* Avatar with first letter */}
                <Avatar
                    size={60}
                    radius="xl"
                    color="blue"
                    className="font-bold text-xl"
                >
                    {avatarLetter}
                </Avatar>

                {/* Name + Verified + Invite Code */}
                <div className="flex-1">
                    <Group gap={4} align="center">
                        <Text fw={600} size="lg" className="text-gray-900">
                            {name}
                        </Text>
                        {/* Verified Checkmark */}
                        <svg
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                            className="text-blue-600"
                        >
                            <path
                                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
                                fill="currentColor"
                            />
                        </svg>
                    </Group>

                    {/* <Text size="sm" c="dimmed" mt={2}>
                        Invite Code:{' '}
                        <span className="font-mono font-semibold text-gray-800">{inviteCode}</span>
                    </Text> */}
                </div>
            </Group>

            {/* <Group mt="md" justify="flex-end" gap="sm" align="center">
                <CopyButton value={inviteCode}>
                    {({ copied, copy }) => (
                        <Tooltip label={copied ? 'Copied!' : 'Copy code'} withArrow position="top">
                            <div
                                onClick={copy}
                                className={`
            flex items-center gap-1.5 px-3 py-1.5 rounded-md cursor-pointer
            transition-all duration-200 select-none
            ${copied ? 'bg-teal-50 text-[#002FD4]' : 'text-[#002FD4] hover:bg-gray-200'}
          `}
                                style={{
                                    fontFamily: '"Poppins", sans-serif',
                                    fontWeight: 500,
                                    fontSize: 13,
                                    lineHeight: '20px',
                                }}
                            >
                                <Copy
                                    style={{
                                        width: rem(18),
                                        height: rem(18),
                                        color: '#002FD4',
                                    }}
                                />
                                <Text
                                    size="xs"
                                    fw={500}
                                    style={{
                                        fontSize: 13,
                                        lineHeight: '20px',
                                        color: '#002FD4',
                                        margin: 0,
                                    }}
                                    className="align-middle"
                                >
                                    {copied ? 'Copied' : 'Copy'}
                                </Text>
                            </div>
                        </Tooltip>
                    )}
                </CopyButton>

                <Tooltip label="Share" withArrow position="top">
                    <div
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-md cursor-pointer text-[#002FD4] hover:bg-gray-200 transition-all duration-200 select-none"
                        style={{
                            fontFamily: '"Poppins", sans-serif',
                            fontWeight: 500,
                            fontSize: 13,
                            lineHeight: '20px',
                        }}
                    >
                        <Share
                            style={{
                                width: rem(18),
                                height: rem(18),
                                color: '#002FD4',
                            }}
                        />
                        <Text
                            size="xs"
                            fw={500}
                            style={{
                                fontSize: 13,
                                lineHeight: '20px',
                                color: '#002FD4',
                                margin: 0,
                            }}
                            className="align-middle"
                        >
                            Share
                        </Text>
                    </div>
                </Tooltip>
            </Group> */}
        </div>
    );
}
