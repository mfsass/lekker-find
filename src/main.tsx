import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { clarity } from 'react-microsoft-clarity'
import './index.css'
import App from './App'

// Microsoft Clarity Initialization
const CLARITY_PROJECT_ID = 'utj831zd2w';
clarity.init(CLARITY_PROJECT_ID);

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <App />
    </StrictMode>,
)
