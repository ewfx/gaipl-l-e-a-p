import React from 'react';
import { cn } from '@/lib/utils';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'bot';
  timestamp: Date;
  severity?: 'info' | 'warning' | 'critical' | 'resolved';
}

interface ChatMessageProps {
  message: Message;
  isAnimated?: boolean;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, isAnimated = true }) => {
  const isUser = message.role === 'user';
  
  const getSeverityIcon = () => {
    if (isUser) return null;
    
    switch (message.severity) {
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-amber-500" />;
      case 'critical':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'resolved':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'info':
      default:
        return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const formatContent = (content: string) => {
    console.log('Raw content:', content); // Debug log to see what we're getting
    
    try {
      const jsonData = JSON.parse(content);
      console.log('Parsed JSON:', jsonData); // Debug log to see parsed data
      
      // Handle CI Health Check response (simplified condition)
      if (jsonData.response && jsonData.response.ci) {
        const { response } = jsonData;
        return (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
              {response.prefix}: <span className="text-blue-600 dark:text-blue-400">{response.ci}</span>
            </h3>
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Health Status:</span>
                <span className={cn(
                  "px-2 py-1 rounded-full text-xs font-medium",
                  response.health_status === "Healthy" && "bg-green-100 text-green-800",
                  response.health_status === "Degraded" && "bg-amber-100 text-amber-800",
                  response.health_status === "Critical" && "bg-red-100 text-red-800"
                )}>
                  {response.health_status}
                </span>
              </div>
              
              <div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-1">Details:</span>
                <p className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 p-2 rounded-md">
                  {response.details}
                </p>
              </div>
              
              <div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Dashboard:</span>
                <a 
                  href={response.dashboard} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-sm text-blue-600 hover:underline dark:text-blue-400 ml-2"
                >
                  {response.dashboard}
                </a>
              </div>
              
              <div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-1">Recent Updates:</span>
                <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                  {response.recent_updates}
                </p>
              </div>
              
              {(response.dependencies.upstream.length > 0 || response.dependencies.downstream.length > 0) && (
                <div className="mt-4">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300 block mb-2">Dependencies:</span>
                  <div className="border rounded-md overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="bg-gray-50 dark:bg-gray-900 text-gray-700 dark:text-gray-300">Type</TableHead>
                          <TableHead className="bg-gray-50 dark:bg-gray-900 text-gray-700 dark:text-gray-300">CI</TableHead>
                          <TableHead className="bg-gray-50 dark:bg-gray-900 text-gray-700 dark:text-gray-300">Relationship</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {response.dependencies.upstream.map((dep: any, index: number) => (
                          <TableRow key={`upstream-${index}`} className="hover:bg-gray-50 dark:hover:bg-gray-900">
                            <TableCell className="text-sm">Upstream</TableCell>
                            <TableCell className="text-sm">{dep.ci}</TableCell>
                            <TableCell className="text-sm">{dep.relationship} ({dep.type})</TableCell>
                          </TableRow>
                        ))}
                        {response.dependencies.downstream.map((dep: any, index: number) => (
                          <TableRow key={`downstream-${index}`} className="hover:bg-gray-50 dark:hover:bg-gray-900">
                            <TableCell className="text-sm">Downstream</TableCell>
                            <TableCell className="text-sm">{dep.ci}</TableCell>
                            <TableCell className="text-sm">{dep.relationship} ({dep.type})</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      }
      
      // Existing JSON handling for incidents list
      if (jsonData.incidents && Array.isArray(jsonData.incidents)) {
        return (
          <div>
            <p className="mb-2">{jsonData.message || 'Incidents with CI Health'}</p>
            <div className="border rounded overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[120px]">Incident ID</TableHead>
                    <TableHead>CI Name</TableHead>
                    <TableHead className="w-[100px]">Status</TableHead>
                    <TableHead className="w-[100px]">CI Health</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jsonData.incidents.map((incident: any, index: number) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{incident.incident_id}</TableCell>
                      <TableCell>{incident.ci}</TableCell>
                      <TableCell>
                        <span className={cn(
                          "px-2 py-1 rounded-full text-xs font-medium",
                          incident.status === "New" && "bg-blue-100 text-blue-800",
                          incident.status === "In Progress" && "bg-amber-100 text-amber-800",
                          incident.status === "Resolved" && "bg-green-100 text-green-800",
                          incident.status === "Critical" && "bg-red-100 text-red-800"
                        )}>
                          {incident.status}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className={cn(
                          "px-2 py-1 rounded-full text-xs font-medium",
                          incident.ci_health === "Healthy" && "bg-green-100 text-green-800",
                          incident.ci_health === "Degraded" && "bg-amber-100 text-amber-800",
                          incident.ci_health === "Warning" && "bg-amber-100 text-amber-800",
                          incident.ci_health === "Critical" && "bg-red-100 text-red-800"
                        )}>
                          {incident.ci_health}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <div className="mt-3">
              <details className="text-sm">
                <summary className="cursor-pointer font-medium text-gray-700">Show Details</summary>
                <div className="mt-2 pl-3 border-l-2 border-gray-200">
                  {jsonData.incidents.map((incident: any, index: number) => (
                    <div key={index} className="mb-3">
                      <h4 className="font-medium">{incident.incident_id} - {incident.ci}</h4>
                      <p className="text-gray-600">{incident.details}</p>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          </div>
        );
      }
    } catch (e) {
      console.error('JSON parsing error:', e); // Log parsing errors
      // Fallback for non-JSON content
    }

    // Existing text-based formatting logic
    if (content.includes('Found') && content.includes('open incidents') && content.includes('INC')) {
      const lines = content.split('\n');
      const titleLine = lines[0];
      
      const incidents = lines.slice(1).filter(line => line.trim().startsWith('-')).map(line => {
        const match = line.trim().replace('- ', '').match(/^(INC\d+): (.*) \((.*)\)$/);
        if (match) {
          return {
            id: match[1],
            description: match[2],
            status: match[3]
          };
        }
        return null;
      }).filter(Boolean);
      
      if (incidents.length > 0) {
        return (
          <div>
            <p className="mb-2">{titleLine}</p>
            <div className="border rounded overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[120px]">Incident ID</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="w-[120px]">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {incidents.map((incident: any, index: number) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{incident.id}</TableCell>
                      <TableCell>{incident.description}</TableCell>
                      <TableCell>
                        <span className={cn(
                          "px-2 py-1 rounded-full text-xs font-medium",
                          incident.status === "New" && "bg-blue-100 text-blue-800",
                          incident.status === "In Progress" && "bg-amber-100 text-amber-800",
                          incident.status === "Resolved" && "bg-green-100 text-green-800",
                          incident.status === "Critical" && "bg-red-100 text-red-800"
                        )}>
                          {incident.status}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        );
      }
    }
    
    return (
      <div>
        {content.split('\n').map((line, index) => (
          <div key={index}>
            {line}
            {index < content.split('\n').length - 1 && <br />}
          </div>
        ))}
      </div>
    );
  };
  
  return (
    <div 
      className={cn(
        isUser ? 'message-user' : 'message-bot',
        !isUser && message.severity === 'warning' && 'border-l-4 border-amber-500',
        !isUser && message.severity === 'critical' && 'border-l-4 border-red-500',
        !isUser && message.severity === 'resolved' && 'border-l-4 border-green-500',
        !isUser && message.severity === 'info' && 'border-l-4 border-blue-500',
        isAnimated ? 'opacity-0' : 'opacity-100',
        'transition-all duration-300'
      )}
      style={{ 
        animationDelay: isAnimated ? '100ms' : '0ms',
      }}
    >
      {!isUser && (
        <div className="flex items-center gap-2 mb-2">
          {getSeverityIcon()}
          <span className="font-medium">
            {message.severity === 'warning' ? 'Warning' : 
             message.severity === 'critical' ? 'Critical Alert' : 
             message.severity === 'resolved' ? 'Resolved' : 'Info'}
          </span>
        </div>
      )}
      <div className="text-sm md:text-base overflow-x-auto">{formatContent(message.content)}</div>
      <div className="text-xs mt-1 opacity-70">
        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </div>
    </div>
  );
};

export default ChatMessage;