import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { setupAuth, isAuthenticated } from "./replitAuth";
import { spawn } from "child_process";
import path from "path";

export async function registerRoutes(app: Express): Promise<Server> {
  // Auth middleware
  await setupAuth(app);

  // Auth routes
  app.get('/api/auth/user', isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.user.claims.sub;
      const user = await storage.getUser(userId);
      res.json(user);
    } catch (error) {
      console.error("Error fetching user:", error);
      res.status(500).json({ message: "Failed to fetch user" });
    }
  });

  // put application routes here
  // prefix all routes with /api

  // use storage to perform CRUD operations on the storage interface
  // e.g. storage.getUser(id) or storage.upsertUser(user)

  // Crypto Signal Analysis Route
  app.post('/api/analyze', async (req, res) => {
    try {
      const { pair, timeframe = '15m' } = req.body;
      
      if (!pair) {
        return res.status(400).json({ error: 'Trading pair is required' });
      }

      // Call Python analysis script
      const pythonScript = path.join(process.cwd(), 'python_backend', 'analyze_pair.py');
      const python = spawn('python', [pythonScript, pair, timeframe]);
      
      let output = '';
      let errorOutput = '';
      
      python.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      python.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });
      
      python.on('close', (code) => {
        if (code !== 0) {
          console.error('Python script error:', errorOutput);
          return res.status(500).json({
            error: 'Analysis failed',
            details: errorOutput
          });
        }
        
        try {
          const result = JSON.parse(output);
          res.json(result);
        } catch (parseError) {
          console.error('Failed to parse Python output:', output);
          res.status(500).json({
            error: 'Failed to parse analysis result'
          });
        }
      });
      
    } catch (error) {
      console.error('Analysis route error:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  });

  // Get supported trading pairs
  app.get('/api/pairs', (req, res) => {
    const popularPairs = [
      'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT',
      'BNBUSDT', 'SOLUSDT', 'MATICUSDT', 'AVAXUSDT', 'LTCUSDT',
      'XRPUSDT', 'ATOMUSDT', 'ALGOUSDT', 'VETUSDT', 'FILUSDT'
    ];
    
    res.json({
      pairs: popularPairs,
      supported_timeframes: ['15m'],
      default_timeframe: '15m'
    });
  });

  const httpServer = createServer(app);

  return httpServer;
}
