// Shared design tokens for web and React Native platforms
// This ensures identical visual design across all platforms

import { APP_CONFIG } from './app-config';

// CSS Variables for Web
export const CSS_VARIABLES = `
  :root {
    /* Primary Colors */
    --color-chat-start: #00c6ff;
    --color-chat-end: #0072ff;
    --color-translate-start: #ff006e;
    --color-translate-end: #8338ec;
    --color-voice-start: #7209b7;
    --color-voice-end: #2d1b69;
    --color-phone-start: #ff8a00;
    --color-phone-end: #e52e71;
    --color-main-start: #667eea;
    --color-main-end: #764ba2;

    /* Status Colors */
    --color-success: #4CAF50;
    --color-error: #F44336;
    --color-warning: #FF9800;
    --color-info: #2196F3;
    --color-connecting: #FF9800;
    --color-connected: #4CAF50;
    --color-disconnected: #F44336;

    /* Neutral Colors */
    --color-white: #FFFFFF;
    --color-black: #000000;
    --color-gray-100: #F5F5F5;
    --color-gray-200: #EEEEEE;
    --color-gray-300: #E0E0E0;
    --color-gray-400: #BDBDBD;
    --color-gray-500: #9E9E9E;
    --color-gray-600: #757575;
    --color-gray-700: #616161;
    --color-gray-800: #424242;
    --color-gray-900: #212121;

    /* Typography */
    --font-size-hero: 36px;
    --font-size-title: 28px;
    --font-size-heading: 24px;
    --font-size-subheading: 20px;
    --font-size-body: 16px;
    --font-size-caption: 14px;
    --font-size-small: 12px;
    --font-size-tiny: 10px;

    --font-weight-light: 300;
    --font-weight-normal: 400;
    --font-weight-medium: 500;
    --font-weight-semibold: 600;
    --font-weight-bold: 700;
    --font-weight-heavy: 800;

    --line-height-tight: 1.2;
    --line-height-normal: 1.4;
    --line-height-relaxed: 1.6;
    --line-height-loose: 1.8;

    /* Spacing */
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
    --spacing-xxl: 48px;
    --spacing-xxxl: 64px;

    /* Border Radius */
    --border-radius-sm: 4px;
    --border-radius-md: 8px;
    --border-radius-lg: 12px;
    --border-radius-xl: 16px;
    --border-radius-xxl: 20px;
    --border-radius-round: 9999px;

    /* Shadows */
    --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
    --shadow-md: 0 4px 8px rgba(0,0,0,0.12);
    --shadow-lg: 0 8px 16px rgba(0,0,0,0.15);
    --shadow-xl: 0 12px 24px rgba(0,0,0,0.18);
    --shadow-xxl: 0 20px 40px rgba(0,0,0,0.2);

    /* Animations */
    --animation-duration: 300ms;
    --animation-timing: cubic-bezier(0.4, 0, 0.2, 1);
  }
`;

// React Native StyleSheet compatible tokens
export const STYLE_TOKENS = {
  colors: APP_CONFIG.DESIGN.colors,
  typography: APP_CONFIG.DESIGN.typography,
  spacing: APP_CONFIG.DESIGN.spacing,
  borderRadius: APP_CONFIG.DESIGN.borderRadius,
  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 2,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.12,
      shadowRadius: 8,
      elevation: 4,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.15,
      shadowRadius: 16,
      elevation: 8,
    },
    xl: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 12 },
      shadowOpacity: 0.18,
      shadowRadius: 24,
      elevation: 12,
    },
    xxl: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 20 },
      shadowOpacity: 0.2,
      shadowRadius: 40,
      elevation: 20,
    },
  },
};

// Common component styles that work on both platforms
export const COMMON_STYLES = {
  // Layout
  container: {
    flex: 1,
    backgroundColor: STYLE_TOKENS.colors.neutral.white,
  },
  centerContent: {
    justifyContent: 'center' as const,
    alignItems: 'center' as const,
  },
  row: {
    flexDirection: 'row' as const,
    alignItems: 'center' as const,
  },
  column: {
    flexDirection: 'column' as const,
  },
  spaceBetween: {
    justifyContent: 'space-between' as const,
  },
  spaceAround: {
    justifyContent: 'space-around' as const,
  },
  spaceEvenly: {
    justifyContent: 'space-evenly' as const,
  },

  // Typography
  heroText: {
    fontSize: STYLE_TOKENS.typography.sizes.hero,
    fontWeight: STYLE_TOKENS.typography.weights.bold as any,
    lineHeight: STYLE_TOKENS.typography.sizes.hero * STYLE_TOKENS.typography.lineHeights.tight,
  },
  titleText: {
    fontSize: STYLE_TOKENS.typography.sizes.title,
    fontWeight: STYLE_TOKENS.typography.weights.bold as any,
    lineHeight: STYLE_TOKENS.typography.sizes.title * STYLE_TOKENS.typography.lineHeights.tight,
  },
  headingText: {
    fontSize: STYLE_TOKENS.typography.sizes.heading,
    fontWeight: STYLE_TOKENS.typography.weights.semibold as any,
    lineHeight: STYLE_TOKENS.typography.sizes.heading * STYLE_TOKENS.typography.lineHeights.normal,
  },
  subheadingText: {
    fontSize: STYLE_TOKENS.typography.sizes.subheading,
    fontWeight: STYLE_TOKENS.typography.weights.medium as any,
    lineHeight: STYLE_TOKENS.typography.sizes.subheading * STYLE_TOKENS.typography.lineHeights.normal,
  },
  bodyText: {
    fontSize: STYLE_TOKENS.typography.sizes.body,
    fontWeight: STYLE_TOKENS.typography.weights.normal as any,
    lineHeight: STYLE_TOKENS.typography.sizes.body * STYLE_TOKENS.typography.lineHeights.relaxed,
  },
  captionText: {
    fontSize: STYLE_TOKENS.typography.sizes.caption,
    fontWeight: STYLE_TOKENS.typography.weights.normal as any,
    lineHeight: STYLE_TOKENS.typography.sizes.caption * STYLE_TOKENS.typography.lineHeights.normal,
  },
  smallText: {
    fontSize: STYLE_TOKENS.typography.sizes.small,
    fontWeight: STYLE_TOKENS.typography.weights.normal as any,
    lineHeight: STYLE_TOKENS.typography.sizes.small * STYLE_TOKENS.typography.lineHeights.normal,
  },

  // Cards and Surfaces
  card: {
    backgroundColor: STYLE_TOKENS.colors.neutral.white,
    borderRadius: STYLE_TOKENS.borderRadius.lg,
    padding: STYLE_TOKENS.spacing.md,
    ...STYLE_TOKENS.shadows.md,
  },
  cardElevated: {
    backgroundColor: STYLE_TOKENS.colors.neutral.white,
    borderRadius: STYLE_TOKENS.borderRadius.lg,
    padding: STYLE_TOKENS.spacing.lg,
    ...STYLE_TOKENS.shadows.lg,
  },
  surface: {
    backgroundColor: STYLE_TOKENS.colors.neutral.gray100,
    borderRadius: STYLE_TOKENS.borderRadius.md,
    padding: STYLE_TOKENS.spacing.md,
  },

  // Buttons
  buttonBase: {
    borderRadius: STYLE_TOKENS.borderRadius.lg,
    paddingVertical: STYLE_TOKENS.spacing.md,
    paddingHorizontal: STYLE_TOKENS.spacing.lg,
    alignItems: 'center' as const,
    justifyContent: 'center' as const,
    minHeight: 48,
  },
  buttonPrimary: {
    backgroundColor: STYLE_TOKENS.colors.primary.main.start,
    ...STYLE_TOKENS.shadows.md,
  },
  buttonSecondary: {
    backgroundColor: STYLE_TOKENS.colors.neutral.gray200,
    borderWidth: 1,
    borderColor: STYLE_TOKENS.colors.neutral.gray300,
  },
  buttonText: {
    fontSize: STYLE_TOKENS.typography.sizes.body,
    fontWeight: STYLE_TOKENS.typography.weights.semibold as any,
    color: STYLE_TOKENS.colors.neutral.white,
  },
  buttonTextSecondary: {
    fontSize: STYLE_TOKENS.typography.sizes.body,
    fontWeight: STYLE_TOKENS.typography.weights.semibold as any,
    color: STYLE_TOKENS.colors.neutral.gray700,
  },

  // Inputs
  inputBase: {
    borderWidth: 1,
    borderColor: STYLE_TOKENS.colors.neutral.gray300,
    borderRadius: STYLE_TOKENS.borderRadius.md,
    paddingVertical: STYLE_TOKENS.spacing.md,
    paddingHorizontal: STYLE_TOKENS.spacing.md,
    fontSize: STYLE_TOKENS.typography.sizes.body,
    backgroundColor: STYLE_TOKENS.colors.neutral.white,
    minHeight: 48,
  },
  inputFocused: {
    borderColor: STYLE_TOKENS.colors.primary.main.start,
    borderWidth: 2,
    ...STYLE_TOKENS.shadows.sm,
  },
  inputError: {
    borderColor: STYLE_TOKENS.colors.status.error,
  },

  // Status indicators
  statusSuccess: {
    backgroundColor: STYLE_TOKENS.colors.status.success,
  },
  statusError: {
    backgroundColor: STYLE_TOKENS.colors.status.error,
  },
  statusWarning: {
    backgroundColor: STYLE_TOKENS.colors.status.warning,
  },
  statusInfo: {
    backgroundColor: STYLE_TOKENS.colors.status.info,
  },

  // Utility classes
  marginTop: (size: keyof typeof STYLE_TOKENS.spacing) => ({
    marginTop: STYLE_TOKENS.spacing[size],
  }),
  marginBottom: (size: keyof typeof STYLE_TOKENS.spacing) => ({
    marginBottom: STYLE_TOKENS.spacing[size],
  }),
  marginLeft: (size: keyof typeof STYLE_TOKENS.spacing) => ({
    marginLeft: STYLE_TOKENS.spacing[size],
  }),
  marginRight: (size: keyof typeof STYLE_TOKENS.spacing) => ({
    marginRight: STYLE_TOKENS.spacing[size],
  }),
  paddingTop: (size: keyof typeof STYLE_TOKENS.spacing) => ({
    paddingTop: STYLE_TOKENS.spacing[size],
  }),
  paddingBottom: (size: keyof typeof STYLE_TOKENS.spacing) => ({
    paddingBottom: STYLE_TOKENS.spacing[size],
  }),
  paddingLeft: (size: keyof typeof STYLE_TOKENS.spacing) => ({
    paddingLeft: STYLE_TOKENS.spacing[size],
  }),
  paddingRight: (size: keyof typeof STYLE_TOKENS.spacing) => ({
    paddingRight: STYLE_TOKENS.spacing[size],
  }),
};

// Service-specific gradient creators
export const createServiceGradient = (serviceId: string) => {
  const service = APP_CONFIG.SERVICES.find(s => s.id === serviceId);
  if (!service) return [APP_CONFIG.DESIGN.colors.primary.main.start, APP_CONFIG.DESIGN.colors.primary.main.end];
  return [service.gradient.start, service.gradient.end];
};

// Web CSS gradient generator
export const createCSSGradient = (serviceId: string, direction = '135deg') => {
  const colors = createServiceGradient(serviceId);
  return `linear-gradient(${direction}, ${colors[0]}, ${colors[1]})`;
};

// Responsive breakpoints for web
export const BREAKPOINTS = {
  mobile: '(max-width: 768px)',
  tablet: '(min-width: 769px) and (max-width: 1024px)',
  desktop: '(min-width: 1025px)',
  largeDesktop: '(min-width: 1440px)',
};

// Animation presets
export const ANIMATIONS = {
  fadeIn: {
    opacity: 0,
    transform: 'translateY(20px)',
    transition: 'opacity 300ms ease, transform 300ms ease',
  },
  fadeInVisible: {
    opacity: 1,
    transform: 'translateY(0)',
  },
  slideUp: {
    transform: 'translateY(100%)',
    transition: 'transform 300ms cubic-bezier(0.4, 0, 0.2, 1)',
  },
  slideUpVisible: {
    transform: 'translateY(0)',
  },
  scaleIn: {
    transform: 'scale(0.9)',
    opacity: 0,
    transition: 'transform 300ms ease, opacity 300ms ease',
  },
  scaleInVisible: {
    transform: 'scale(1)',
    opacity: 1,
  },
};

export default {
  CSS_VARIABLES,
  STYLE_TOKENS,
  COMMON_STYLES,
  createServiceGradient,
  createCSSGradient,
  BREAKPOINTS,
  ANIMATIONS,
};
