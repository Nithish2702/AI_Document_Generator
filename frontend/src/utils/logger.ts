/**
 * Frontend Logger Utility
 * Provides consistent logging across the application
 */

type LogLevel = 'info' | 'warn' | 'error' | 'success' | 'debug';

class Logger {
  private isDevelopment = import.meta.env.DEV;

  private formatMessage(level: LogLevel, message: string, data?: any): string {
    const timestamp = new Date().toLocaleTimeString();
    const emoji = this.getEmoji(level);
    return `${emoji} [${timestamp}] ${message}`;
  }

  private getEmoji(level: LogLevel): string {
    const emojis = {
      info: '📘',
      warn: '⚠️',
      error: '❌',
      success: '✅',
      debug: '🔍'
    };
    return emojis[level];
  }

  private log(level: LogLevel, message: string, data?: any) {
    if (!this.isDevelopment && level === 'debug') return;

    const formattedMessage = this.formatMessage(level, message, data);

    switch (level) {
      case 'error':
        console.error(formattedMessage, data || '');
        break;
      case 'warn':
        console.warn(formattedMessage, data || '');
        break;
      case 'success':
      case 'info':
        console.info(formattedMessage, data || '');
        break;
      case 'debug':
        console.log(formattedMessage, data || '');
        break;
    }
  }

  info(message: string, data?: any) {
    this.log('info', message, data);
  }

  warn(message: string, data?: any) {
    this.log('warn', message, data);
  }

  error(message: string, error?: any) {
    this.log('error', message, error);
  }

  success(message: string, data?: any) {
    this.log('success', message, data);
  }

  debug(message: string, data?: any) {
    this.log('debug', message, data);
  }

  // API request logging
  apiRequest(method: string, url: string, data?: any) {
    this.info(`🌐 API ${method} ${url}`, data);
  }

  apiResponse(method: string, url: string, status: number, duration: number) {
    const emoji = status >= 200 && status < 300 ? '✅' : '❌';
    this.info(`${emoji} API ${method} ${url} - ${status} (${duration}ms)`);
  }

  apiError(method: string, url: string, error: any) {
    this.error(`❌ API ${method} ${url} failed`, error);
  }
}

export const logger = new Logger();
