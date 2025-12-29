import React, { useEffect, useState, useRef, useMemo } from 'react';
import './LoadingScreen.css';
import { getLoadingWords } from '../../data/loadingWords';


interface LoadingScreenProps {
    isVisible: boolean;
    touristLevel: number | null;
    intent: string | null;
    onComplete: () => void;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({ isVisible, touristLevel, intent, onComplete }) => {
    const [isDone, setIsDone] = useState(false);
    // Matches animation cycle closer (4s per loop, so 4s or 8s is good)
    const duration = useRef(4000);

    // Select curated words based on tourist level & intent
    const sessionWords = useMemo(() => {
        return getLoadingWords(touristLevel, intent);
    }, [isVisible, touristLevel, intent]);

    useEffect(() => {
        if (isVisible) {
            if (document.body) {
                document.body.style.overflow = 'hidden';
            }

            const timeoutId = setTimeout(() => {
                setIsDone(true);
                setTimeout(() => {
                    if (document.body) {
                        document.body.style.overflow = '';
                    }
                    onComplete();
                }, 1000); // Wait a second on "lekker!"
            }, duration.current);

            return () => {
                clearTimeout(timeoutId);
                if (document.body) {
                    document.body.style.overflow = '';
                }
            };
        } else {
            setIsDone(false);
        }
    }, [isVisible, onComplete]);

    if (!isVisible) return null;

    return (
        <div className="loading-screen-container">
            <div className="loader-card">
                {isDone ? (
                    <div className="loader" style={{ justifyContent: 'center' }}>
                        <span className="completion-message">lekker!</span>
                    </div>
                ) : (
                    <div className="loader">
                        <p>Loading</p>

                        <div className="words">
                            {sessionWords.map((word, i) => (
                                <span key={i} className="word">{word}</span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
