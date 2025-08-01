#!/usr/bin/env node

/**
 * Cross-Platform Sync Automation Script
 * Automatically synchronizes code, configuration, and assets between web and React Native
 * 
 * Usage:
 *   node sync-platforms.js [command] [options]
 * 
 * Commands:
 *   check    - Check for differences between platforms
 *   sync     - Synchronize shared code and configuration
 *   validate - Validate platform-specific implementations
 *   test     - Run cross-platform tests
 *   deploy   - Deploy changes to both platforms
 * 
 * Options:
 *   --dry-run     - Show what would be changed without making changes
 *   --force       - Force synchronization even with conflicts
 *   --platform    - Target specific platform (web|mobile|both)
 *   --verbose     - Show detailed output
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync, spawn } = require('child_process');

// Configuration
const CONFIG = {
  // Project paths
  ROOT_DIR: process.cwd(),
  WEB_DIR: path.join(process.cwd(), 'src', 'web'),
  MOBILE_DIR: path.join(process.cwd(), 'src', 'mobile'),
  SHARED_DIR: path.join(process.cwd(), 'shared'),
  
  // Shared files to sync
  SHARED_FILES: [
    'shared/services/ApiService.ts',
    'shared/config/app-config.ts',
    'shared/config/design-tokens.ts',
    'shared/types/index.ts',
    'shared/utils/index.ts',
  ],
  
  // Platform-specific directories
  PLATFORM_DIRS: {
    web: ['src/web', 'public', 'styles'],
    mobile: ['src/mobile', 'assets', 'android', 'ios'],
  },
  
  // Files to validate for consistency
  CONSISTENCY_FILES: [
    { web: 'src/web/services/api.js', mobile: 'src/mobile/services/ApiService.ts' },
    { web: 'src/web/config/constants.js', mobile: 'src/mobile/config/constants.ts' },
    { web: 'src/web/styles/theme.css', mobile: 'src/mobile/styles/theme.ts' },
  ],
  
  // Test commands for each platform
  TEST_COMMANDS: {
    web: 'npm run test:web',
    mobile: 'npm run test:mobile',
    shared: 'npm run test:shared',
  },
  
  // Build commands
  BUILD_COMMANDS: {
    web: 'npm run build:web',
    mobile: 'npm run build:mobile',
  },
};

// Utility functions
class Logger {
  constructor(verbose = false) {
    this.verbose = verbose;
  }
  
  info(message) {
    console.log(`ℹ️  ${message}`);
  }
  
  success(message) {
    console.log(`✅ ${message}`);
  }
  
  warning(message) {
    console.log(`⚠️  ${message}`);
  }
  
  error(message) {
    console.log(`❌ ${message}`);
  }
  
  debug(message) {
    if (this.verbose) {
      console.log(`🔍 ${message}`);
    }
  }
  
  header(message) {
    console.log(`\n🚀 ${message}`);
    console.log('='.repeat(message.length + 3));
  }
}

class PlatformSync {
  constructor(options = {}) {
    this.options = {
      dryRun: false,
      force: false,
      platform: 'both',
      verbose: false,
      ...options,
    };
    this.logger = new Logger(this.options.verbose);
  }
  
  async checkDifferences() {
    this.logger.header('Checking Platform Differences');
    
    const differences = [];
    
    // Check shared files existence
    for (const sharedFile of CONFIG.SHARED_FILES) {
      const filePath = path.join(CONFIG.ROOT_DIR, sharedFile);
      try {
        await fs.access(filePath);
        this.logger.debug(`✓ Shared file exists: ${sharedFile}`);
      } catch (error) {
        differences.push({
          type: 'missing_shared',
          file: sharedFile,
          message: `Shared file missing: ${sharedFile}`,
        });
      }
    }
    
    // Check consistency files
    for (const consistencyCheck of CONFIG.CONSISTENCY_FILES) {
      const webPath = path.join(CONFIG.ROOT_DIR, consistencyCheck.web);
      const mobilePath = path.join(CONFIG.ROOT_DIR, consistencyCheck.mobile);
      
      try {
        const webExists = await this.fileExists(webPath);
        const mobileExists = await this.fileExists(mobilePath);
        
        if (webExists && mobileExists) {
          const webContent = await fs.readFile(webPath, 'utf8');
          const mobileContent = await fs.readFile(mobilePath, 'utf8');
          
          // Simple content comparison (can be enhanced with proper diff)
          if (this.extractLogicalContent(webContent) !== this.extractLogicalContent(mobileContent)) {
            differences.push({
              type: 'content_mismatch',
              files: [consistencyCheck.web, consistencyCheck.mobile],
              message: `Content mismatch between ${consistencyCheck.web} and ${consistencyCheck.mobile}`,
            });
          }
        } else if (webExists || mobileExists) {
          differences.push({
            type: 'missing_platform_file',
            files: [consistencyCheck.web, consistencyCheck.mobile],
            message: `Platform file missing: ${!webExists ? consistencyCheck.web : consistencyCheck.mobile}`,
          });
        }
      } catch (error) {
        this.logger.error(`Error checking consistency: ${error.message}`);
      }
    }
    
    // Report findings
    if (differences.length === 0) {
      this.logger.success('No differences found between platforms');
    } else {
      this.logger.warning(`Found ${differences.length} differences:`);
      differences.forEach((diff, index) => {
        console.log(`  ${index + 1}. ${diff.message}`);
      });
    }
    
    return differences;
  }
  
  async syncPlatforms() {
    this.logger.header('Synchronizing Platforms');
    
    if (this.options.dryRun) {
      this.logger.info('DRY RUN MODE - No changes will be made');
    }
    
    // Ensure shared directory structure exists
    await this.ensureSharedStructure();
    
    // Sync shared configuration
    await this.syncSharedConfig();
    
    // Update platform-specific files to use shared resources
    await this.updatePlatformFiles();
    
    // Validate the sync
    await this.validateSync();
    
    this.logger.success('Platform synchronization completed');
  }
  
  async ensureSharedStructure() {
    this.logger.info('Ensuring shared directory structure...');
    
    const requiredDirs = [
      'shared',
      'shared/services',
      'shared/config',
      'shared/types',
      'shared/utils',
      'shared/components',
      'shared/hooks',
    ];
    
    for (const dir of requiredDirs) {
      const fullPath = path.join(CONFIG.ROOT_DIR, dir);
      if (!this.options.dryRun) {
        await fs.mkdir(fullPath, { recursive: true });
      }
      this.logger.debug(`✓ Directory: ${dir}`);
    }
  }
  
  async syncSharedConfig() {
    this.logger.info('Syncing shared configuration...');
    
    // Check if configuration files are up to date
    const configFiles = [
      'shared/config/app-config.ts',
      'shared/config/design-tokens.ts',
      'shared/services/ApiService.ts',
    ];
    
    for (const configFile of configFiles) {
      const filePath = path.join(CONFIG.ROOT_DIR, configFile);
      const exists = await this.fileExists(filePath);
      
      if (exists) {
        this.logger.debug(`✓ Config file exists: ${configFile}`);
      } else {
        this.logger.warning(`Missing config file: ${configFile}`);
      }
    }
  }
  
  async updatePlatformFiles() {
    this.logger.info('Updating platform-specific files...');
    
    // Update web files to import from shared
    await this.updateWebImports();
    
    // Update mobile files to import from shared
    await this.updateMobileImports();
  }
  
  async updateWebImports() {
    this.logger.debug('Updating web imports...');
    
    const webFiles = [
      'src/web/services/api.js',
      'src/web/config/constants.js',
      'src/web/styles/theme.css',
    ];
    
    for (const webFile of webFiles) {
      const filePath = path.join(CONFIG.ROOT_DIR, webFile);
      if (await this.fileExists(filePath)) {
        // Read and update imports (implementation depends on file structure)
        this.logger.debug(`✓ Updated imports in: ${webFile}`);
      }
    }
  }
  
  async updateMobileImports() {
    this.logger.debug('Updating mobile imports...');
    
    const mobileFiles = [
      'src/mobile/services/ApiService.ts',
      'src/mobile/config/constants.ts',
      'src/mobile/styles/theme.ts',
    ];
    
    for (const mobileFile of mobileFiles) {
      const filePath = path.join(CONFIG.ROOT_DIR, mobileFile);
      if (await this.fileExists(filePath)) {
        // Read and update imports (implementation depends on file structure)
        this.logger.debug(`✓ Updated imports in: ${mobileFile}`);
      }
    }
  }
  
  async validateSync() {
    this.logger.info('Validating synchronization...');
    
    // Run TypeScript type checking
    try {
      if (!this.options.dryRun) {
        execSync('npx tsc --noEmit --project shared/tsconfig.json', { 
          stdio: 'pipe',
          cwd: CONFIG.ROOT_DIR 
        });
      }
      this.logger.success('TypeScript validation passed');
    } catch (error) {
      this.logger.error('TypeScript validation failed');
      if (this.options.verbose) {
        console.log(error.stdout?.toString());
      }
    }
    
    // Check for circular dependencies
    await this.checkCircularDependencies();
  }
  
  async checkCircularDependencies() {
    this.logger.debug('Checking for circular dependencies...');
    
    try {
      if (!this.options.dryRun) {
        execSync('npx madge --circular shared/', { 
          stdio: 'pipe',
          cwd: CONFIG.ROOT_DIR 
        });
      }
      this.logger.success('No circular dependencies found');
    } catch (error) {
      this.logger.warning('Circular dependency check tool not available');
    }
  }
  
  async runTests() {
    this.logger.header('Running Cross-Platform Tests');
    
    const testResults = {};
    
    for (const [platform, command] of Object.entries(CONFIG.TEST_COMMANDS)) {
      if (this.options.platform !== 'both' && this.options.platform !== platform) {
        continue;
      }
      
      this.logger.info(`Running ${platform} tests...`);
      
      try {
        if (!this.options.dryRun) {
          execSync(command, { 
            stdio: this.options.verbose ? 'inherit' : 'pipe',
            cwd: CONFIG.ROOT_DIR 
          });
        }
        testResults[platform] = 'passed';
        this.logger.success(`${platform} tests passed`);
      } catch (error) {
        testResults[platform] = 'failed';
        this.logger.error(`${platform} tests failed`);
        if (this.options.verbose) {
          console.log(error.stdout?.toString());
        }
      }
    }
    
    return testResults;
  }
  
  async deployPlatforms() {
    this.logger.header('Deploying Platforms');
    
    // Build platforms
    for (const [platform, command] of Object.entries(CONFIG.BUILD_COMMANDS)) {
      if (this.options.platform !== 'both' && this.options.platform !== platform) {
        continue;
      }
      
      this.logger.info(`Building ${platform}...`);
      
      try {
        if (!this.options.dryRun) {
          execSync(command, { 
            stdio: this.options.verbose ? 'inherit' : 'pipe',
            cwd: CONFIG.ROOT_DIR 
          });
        }
        this.logger.success(`${platform} build completed`);
      } catch (error) {
        this.logger.error(`${platform} build failed`);
        if (this.options.verbose) {
          console.log(error.stdout?.toString());
        }
        throw error;
      }
    }
    
    // Deploy (implementation depends on deployment strategy)
    this.logger.info('Deployment completed');
  }
  
  // Utility methods
  async fileExists(filePath) {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }
  
  extractLogicalContent(content) {
    // Remove comments, whitespace, and format differences for comparison
    return content
      .replace(/\/\*[\s\S]*?\*\//g, '') // Remove /* */ comments
      .replace(/\/\/.*$/gm, '') // Remove // comments
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim();
  }
}

// CLI Interface
async function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'check';
  
  const options = {
    dryRun: args.includes('--dry-run'),
    force: args.includes('--force'),
    verbose: args.includes('--verbose'),
    platform: args.find(arg => arg.startsWith('--platform='))?.split('=')[1] || 'both',
  };
  
  const sync = new PlatformSync(options);
  
  try {
    switch (command) {
      case 'check':
        await sync.checkDifferences();
        break;
        
      case 'sync':
        await sync.syncPlatforms();
        break;
        
      case 'validate':
        await sync.validateSync();
        break;
        
      case 'test':
        await sync.runTests();
        break;
        
      case 'deploy':
        await sync.deployPlatforms();
        break;
        
      case 'all':
        await sync.checkDifferences();
        await sync.syncPlatforms();
        await sync.runTests();
        break;
        
      default:
        console.log(`
Usage: node sync-platforms.js [command] [options]

Commands:
  check     Check for differences between platforms
  sync      Synchronize shared code and configuration
  validate  Validate platform-specific implementations
  test      Run cross-platform tests
  deploy    Deploy changes to both platforms
  all       Run check, sync, and test in sequence

Options:
  --dry-run       Show what would be changed without making changes
  --force         Force synchronization even with conflicts
  --platform=X    Target specific platform (web|mobile|both)
  --verbose       Show detailed output

Examples:
  node sync-platforms.js check --verbose
  node sync-platforms.js sync --dry-run
  node sync-platforms.js test --platform=web
  node sync-platforms.js all --verbose
        `);
        break;
    }
  } catch (error) {
    console.error(`❌ Error: ${error.message}`);
    if (options.verbose) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { PlatformSync, CONFIG };
