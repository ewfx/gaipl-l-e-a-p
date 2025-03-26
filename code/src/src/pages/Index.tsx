
import { motion } from "framer-motion";
import ChatBot from "@/components/ChatBot";
import { Server, Database, Terminal } from "lucide-react";

const Index = () => {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center py-12 px-4 bg-gradient-to-b from-slate-50 to-gray-100 dark:from-slate-900 dark:to-gray-950">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="text-center mb-8"
      >
        <motion.div 
          className="inline-block mb-2 px-3 py-1 bg-indigo-100 dark:bg-indigo-900/30 rounded-full text-indigo-800 dark:text-indigo-200 text-xs font-medium"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.6 }}
        >
          Incident Resolution Assistant
        </motion.div>
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">
          OpsBuddy
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-md mx-auto">
          Accelerate incident resolution with AI-powered analysis and automation
        </p>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
        className="flex justify-center gap-8 mb-8 max-w-2xl"
      >
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-2">
            <Database size={20} className="text-blue-600 dark:text-blue-400" />
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">CMDB Integration</p>
        </div>
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-2">
            <Server size={20} className="text-green-600 dark:text-green-400" />
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">System Monitoring</p>
        </div>
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center mb-2">
            <Terminal size={20} className="text-amber-600 dark:text-amber-400" />
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">Automated Resolution</p>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.8 }}
        className="w-full max-w-4xl"
      >
        <ChatBot initialMessage="Hello! I'm OpsBuddy, your intelligent incident resolution assistant. I can help you monitor systems, investigate issues, and automate resolutions. What can I help you with today?" />
      </motion.div>
      
      <motion.p 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8, duration: 0.6 }}
        className="mt-6 text-sm text-gray-500 dark:text-gray-400"
      >
        Try describing an incident or ask for system status to see OpsBuddy in action.
      </motion.p>
    </div>
  );
};

export default Index;
