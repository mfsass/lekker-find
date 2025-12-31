import { Component, ErrorInfo, ReactNode } from 'react';
import { RefreshCcw } from 'lucide-react';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  private handleRetry = () => {
    // Clear the error state and try to re-render
    // For asset loading errors, a full reload might be better
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary-container">
          <div className="error-content">
            <div className="error-icon-wrapper">
              <span className="error-emoji">😬</span>
            </div>
            <h1 className="error-title">Something is not lekker</h1>
            <p className="error-message">
              We're having a bit of a wobble.
            </p>
            <div className="error-comment">
              we are currently experiencing high volumes, please try again later
            </div>

            <button
              onClick={this.handleRetry}
              className="btn-primary error-retry-btn"
            >
              <RefreshCcw className="icon" size={20} />
              <span>Try again</span>
            </button>

            <div className="error-details">
              {this.state.error?.message.includes('preload') ? (
                <p className="error-subtext">It looks like some assets failed to load. A quick refresh usually fixes this!</p>
              ) : (
                <p className="error-subtext">Our team of penguins has been notified.</p>
              )}
            </div>
          </div>

          <style>{`
            .error-boundary-container {
              min-height: 100vh;
              display: flex;
              align-items: center;
              justify-content: center;
              background: var(--background);
              padding: 2rem;
              text-align: center;
              font-family: var(--font-sans);
            }
            .error-content {
              max-width: 400px;
              width: 100%;
              animation: errorIn 0.5s ease-out;
            }
            .error-emoji {
              font-size: 5rem;
              display: block;
              margin-bottom: 1.5rem;
            }
            .error-title {
              font-size: 2rem;
              font-weight: 700;
              margin-bottom: 1rem;
              color: var(--foreground);
              letter-spacing: -0.02em;
            }
            .error-message {
              font-size: 1.125rem;
              color: var(--muted-foreground);
              margin-bottom: 2rem;
            }
            .error-comment {
              font-size: 0.8125rem;
              color: var(--muted-foreground);
              font-style: italic;
              margin-bottom: 2rem;
              opacity: 0.8;
            }

            .error-retry-btn {
              width: 100%;
              margin-bottom: 1.5rem;
              gap: 0.75rem;
            }
            .error-details {
              opacity: 0.6;
            }
            .error-subtext {
              font-size: 0.8125rem;
              color: var(--muted-foreground);
            }
            @keyframes errorIn {
              from { opacity: 0; transform: translateY(20px); }
              to { opacity: 1; transform: translateY(0); }
            }
          `}</style>
        </div>
      );
    }

    return this.props.children;
  }
}
