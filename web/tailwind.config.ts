import type { Config } from "tailwindcss";

export default {
    darkMode: ["class"],
    content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
  	extend: {
  		colors: {
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			}
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		keyframes: {
  			'line-shadow': {
  				'0%, 100%': {
  					backgroundPosition: '0 0'
  				},
  				'50%': {
  					backgroundPosition: '100% 0'
  				}
  			},
  			'shimmer-slide': {
  				to: {
  					transform: 'translate(calc(100cqw - 100%), 0)'
  				}
  			},
  			'spin-around': {
  				'0%': {
  					transform: 'translateZ(0) rotate(0)'
  				},
  				'15%, 35%': {
  					transform: 'translateZ(0) rotate(90deg)'
  				},
  				'65%, 85%': {
  					transform: 'translateZ(0) rotate(270deg)'
  				},
  				'100%': {
  					transform: 'translateZ(0) rotate(360deg)'
  				}
  			}
  		},
  		animation: {
  			'line-shadow': 'line-shadow 60s linear infinite',
  			'shimmer-slide': 'shimmer-slide var(--speed) ease-in-out infinite alternate',
  			'spin-around': 'spin-around calc(var(--speed) * 2) infinite linear'
  		},
  		typography: {
  			DEFAULT: {
  				css: {
  					maxWidth: 'none',
  					color: '#fff',
  					a: {
  						color: '#3b82f6',
  						'&:hover': {
  							color: '#60a5fa',
  						},
  						textDecoration: 'none',
  					},
  					h1: {
  						color: '#fff',
  						fontWeight: '700',
  						fontSize: '2.25rem',
  						marginBottom: '1rem',
  					},
  					h2: {
  						color: '#fff',
  						fontWeight: '600',
  						fontSize: '1.875rem',
  						marginTop: '2rem',
  						marginBottom: '1rem',
  					},
  					h3: {
  						color: '#fff',
  						fontWeight: '600',
  						fontSize: '1.5rem',
  						marginTop: '1.5rem',
  						marginBottom: '0.75rem',
  					},
  					h4: {
  						color: '#fff',
  						fontWeight: '600',
  						marginTop: '1.5rem',
  						marginBottom: '0.75rem',
  					},
  					p: {
  						color: '#d1d5db',
  						marginTop: '1.25rem',
  						marginBottom: '1.25rem',
  						lineHeight: '1.75',
  					},
  					ul: {
  						color: '#d1d5db',
  						listStyleType: 'disc',
  						paddingLeft: '1.625rem',
  					},
  					ol: {
  						color: '#d1d5db',
  						listStyleType: 'decimal',
  						paddingLeft: '1.625rem',
  					},
  					li: {
  						marginTop: '0.5rem',
  						marginBottom: '0.5rem',
  					},
  					strong: {
  						color: '#fff',
  						fontWeight: '600',
  					},
  					blockquote: {
  						color: '#d1d5db',
  						borderLeftColor: '#374151',
  						borderLeftWidth: '4px',
  						paddingLeft: '1rem',
  						fontStyle: 'italic',
  					},
  					'code::before': {
  						content: '""',
  					},
  					'code::after': {
  						content: '""',
  					},
  					code: {
  						color: '#e5e7eb',
  						backgroundColor: '#1f2937',
  						padding: '0.25rem 0.4rem',
  						borderRadius: '0.25rem',
  						fontWeight: '400',
  						fontSize: '0.875rem',
  					},
  					pre: {
  						backgroundColor: '#1f2937',
  						padding: '1rem',
  						borderRadius: '0.5rem',
  						overflowX: 'auto',
  					},
  					'pre code': {
  						backgroundColor: 'transparent',
  						padding: '0',
  						fontSize: '0.875rem',
  						color: '#e5e7eb',
  						border: 'none',
  					},
  					hr: {
  						borderColor: '#374151',
  						marginTop: '2rem',
  						marginBottom: '2rem',
  					},
  					table: {
  						width: '100%',
  						textAlign: 'left',
  						marginTop: '2rem',
  						marginBottom: '2rem',
  						lineHeight: '1.5',
  					},
  					thead: {
  						borderBottomWidth: '1px',
  						borderBottomColor: '#374151',
  					},
  					'thead th': {
  						color: '#fff',
  						fontWeight: '600',
  						padding: '0.75rem',
  						backgroundColor: '#1f2937',
  					},
  					'tbody tr': {
  						borderBottomWidth: '1px',
  						borderBottomColor: '#374151',
  					},
  					'tbody td': {
  						padding: '0.75rem',
  					},
  					img: {
  						marginTop: '2rem',
  						marginBottom: '2rem',
  						borderRadius: '0.5rem',
  					},
  				},
  			},
  		},
  	}
  },
  plugins: [
    require('tailwind-scrollbar'),
    require("tailwindcss-animate"),
    require('@tailwindcss/typography'),
],
} satisfies Config;