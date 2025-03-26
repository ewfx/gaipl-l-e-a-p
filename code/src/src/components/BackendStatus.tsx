
import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

const BackendStatus: React.FC = () => {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkBackendConnection = async () => {
      try {
        const response = await fetch('http://localhost:5000/query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: 'ping' }),
          // Short timeout to prevent long wait if backend is down
          signal: AbortSignal.timeout(3000)
        });
        setIsConnected(response.ok);
      } catch (error) {
        console.error('Backend connection check failed:', error);
        setIsConnected(false);
      } finally {
        setIsChecking(false);
      }
    };

    checkBackendConnection();
  }, []);

  if (isChecking) {
    return null;
  }

  return (
    <div className={`text-xs flex items-center gap-1 px-2 py-1 rounded-full ${
      isConnected ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 
                   'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400'
    }`}>
      {isConnected ? (
        <>
          <CheckCircle2 size={12} />
          <span>Backend connected</span>
        </>
      ) : (
        <>
          <AlertCircle size={12} />
          <span>Using fallback mode</span>
        </>
      )}
    </div>
  );
};

export default BackendStatus;
