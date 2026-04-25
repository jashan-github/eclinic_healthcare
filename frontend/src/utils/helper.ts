export const formatFee = (fee: number | string, currency?: string) => {
    if (fee === 'N/A') return 'N/A'

    const formattedFee = Number(fee).toLocaleString('en-US', { minimumFractionDigits: 0 })

    if (currency === 'INR' || currency === '₹') {
      return `₹ ${formattedFee}`
    }
    else if( currency === '$' || currency === 'USD'){
      return `$ ${formattedFee}`
    }

    return `XCG ${formattedFee}`
  }

export const formatDate = (dateString: string): string => {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    
    // Check if date is valid
    if (isNaN(date.getTime())) return 'N/A'
    
    // Format as "Jan 13, 2026"
    const options: Intl.DateTimeFormatOptions = { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    }
    return date.toLocaleDateString('en-US', options)
  } catch (error) {
    console.error('Error formatting date:', error)
    return 'N/A'
  }
}

export const formatTime = (timeString: string | undefined | null): string => {
  if (!timeString) return 'N/A'

  const parts = timeString.trim().split(':')
  if (parts.length < 2) return timeString

  const hours = parseInt(parts[0], 10)
  const minutes = parts[1]

  if (isNaN(hours)) return timeString

  const ampm = hours >= 12 ? 'PM' : 'AM'
  const hour12 = hours % 12 || 12

  return `${hour12}:${minutes} ${ampm}`
}

export const formatDateTime = (isoString: string): string => {
  if (!isoString) return "";

  try {
    const date = new Date(isoString);

    // If invalid date, return fallback
    if (isNaN(date.getTime())) {
      return "Invalid date";
    }

    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const year = date.getFullYear();

    let hours = date.getHours();
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const ampm = hours >= 12 ? "PM" : "AM";

    // Convert to 12-hour format
    hours = hours % 12;
    hours = hours === 0 ? 12 : hours;

    const formatted = `${month}-${day}-${year} ${hours}:${minutes} ${ampm}`;

    return formatted;
  } catch (err) {
    console.warn("formatDateTime failed:", err);
    return isoString;
  }
};

export const isEncryptionSupported = 
  typeof window !== 'undefined' &&
  window.location?.protocol === 'https:' &&
  window.crypto?.subtle instanceof Object &&
  typeof window.crypto.subtle?.encrypt === 'function' &&
  typeof window.crypto.subtle?.decrypt === 'function';

