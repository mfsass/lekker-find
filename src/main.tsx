import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { clarity } from 'react-microsoft-clarity'
import './index.css'
import App from './App'
import { PostHogProvider } from 'posthog-js/react'
import { POSTHOG_KEY, POSTHOG_HOST } from './utils/analytics'
import { ErrorBoundary } from './components/ui/ErrorBoundary'

// Microsoft Clarity Initialization
const CLARITY_PROJECT_ID = 'utj831zd2w';
clarity.init(CLARITY_PROJECT_ID);

// Global Error Handler for Asset Loading (e.g. CSS preload errors)
window.addEventListener('error', (event) => {
    // If it's a resource loading error (links, scripts, etc)
    if (event.target instanceof HTMLElement &&
        (event.target.tagName === 'LINK' || event.target.tagName === 'SCRIPT')) {
        const url = (event.target as HTMLScriptElement).src || (event.target as HTMLLinkElement).href;
        console.error('Resource failed to load:', url);

        // If it's a critical chunk/CSS failure, we might want to reload or show error
        if (url && (url.includes('/assets/') || url.includes('.css'))) {
            // We can't easily trigger the React ErrorBoundary from here for a non-JS error,
            // but we can force a reload or check if it's persistent.
            // For now, let the ErrorBoundary catch it if it causes a React crash.
        }
    }
}, true);

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <PostHogProvider
            apiKey={POSTHOG_KEY}
            options={{
                api_host: POSTHOG_HOST,
                session_recording: {
                    maskAllInputs: false,

                }
            }}
        >
            <ErrorBoundary>
                <App />
            </ErrorBoundary>
        </PostHogProvider>
    </StrictMode>,
)
