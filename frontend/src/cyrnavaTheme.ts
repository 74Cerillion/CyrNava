import { createTheme } from '@mantine/core';
import type { CSSVariablesResolver } from '@mantine/core';
import type { Theme } from '@blocknote/mantine';

// One palette serves native controls, Mantine, and BlockNote's portal roots.
export const cyrnavaPalette = {
  'bg-primary': '#050507', 'bg-secondary': '#10121B', 'bg-elevated': '#191D2A',
  'accent-blue': '#3288D0', 'accent-blue-deep': '#205080', 'accent-blue-light': '#A0D0F0',
  'accent-violet': '#7030B0', 'accent-violet-deep': '#301060',
  'metallic-silver': '#A8B8C8', 'text-primary': '#F2F4F8',
  'text-secondary': '#B8C0D0', 'text-muted': '#929BAE',
  'border': '#64788E', 'border-violet': '#9876D0', 'error': '#FFADB8', 'warning': '#F4D58A', 'success': '#56E0AA',
} as const;

export const cyrnavaVariables: CSSVariablesResolver = () => ({
  variables: Object.fromEntries(Object.entries(cyrnavaPalette).map(([name, value]) => [`--cyrnava-${name}`, value])),
  light: {}, dark: {},
});

export const cyrnavaMantineTheme = createTheme({
  fontFamily: 'Inter, system-ui, sans-serif', defaultRadius: 'sm',
  primaryColor: 'blue', primaryShade: 4,
  colors: { dark: ['#F2F4F8', '#B8C0D0', '#929BAE', '#64788E', '#36465B', '#273247', '#191D2A', '#10121B', '#090B12', '#050507'] },
});

export const cyrnavaEditorTheme: Theme = {
  colors: {
    editor: { text: cyrnavaPalette['text-primary'], background: cyrnavaPalette['bg-primary'] },
    menu: { text: cyrnavaPalette['text-primary'], background: cyrnavaPalette['bg-secondary'] },
    tooltip: { text: cyrnavaPalette['text-primary'], background: cyrnavaPalette['bg-elevated'] },
    hovered: { text: cyrnavaPalette['text-primary'], background: '#20314A' },
    selected: { text: cyrnavaPalette['text-primary'], background: cyrnavaPalette['accent-blue-deep'] },
    disabled: { text: cyrnavaPalette['text-muted'], background: cyrnavaPalette['bg-elevated'] },
    border: cyrnavaPalette.border, shadow: '#000000', sideMenu: cyrnavaPalette['text-secondary'],
  },
  fontFamily: 'Inter, system-ui, sans-serif', borderRadius: 6,
};
