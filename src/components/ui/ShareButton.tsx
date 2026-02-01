/**
 * ShareButton Component
 * =====================
 * 
 * Mobile-first share button using navigator.share API.
 * Falls back to clipboard copy on desktop.
 */

import { useState } from 'react';
import { Share2, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShareState, getShareUrl } from '../../utils/shareState';
import { captureShare } from '../../utils/analytics';
import './ShareButton.css';

interface ShareButtonProps {
    state: ShareState;
    venueName?: string;
    className?: string;
}

export function ShareButton({ state, venueName, className = '' }: ShareButtonProps) {
    const [copied, setCopied] = useState(false);
    const [isSharing, setIsSharing] = useState(false);

    const handleShare = async (e?: React.MouseEvent | React.TouchEvent) => {
        if (e) e.stopPropagation();
        if (isSharing) return;
        setIsSharing(true);

        const shareUrl = getShareUrl(state);
        const shareData = {
            title: 'Discover something Lekker',
            text: venueName ? `Check out "${venueName}" on Lekker Find!` : "Here's something lekker to do!",
            url: shareUrl,
        };

        try {
            // Mobile: Use native share sheet (WhatsApp, etc.)
            if (navigator.share && navigator.canShare?.(shareData)) {
                await navigator.share(shareData);
                captureShare?.('native', shareUrl);
            } else {
                // Desktop: Copy to clipboard
                await navigator.clipboard.writeText(shareUrl);
                setCopied(true);
                captureShare?.('clipboard', shareUrl);

                // Reset copied state after 2s
                setTimeout(() => setCopied(false), 2000);
            }
        } catch (error) {
            // User cancelled share or clipboard failed
            if ((error as Error).name !== 'AbortError') {
                console.error('Share failed:', error);
            }
        } finally {
            setIsSharing(false);
        }
    };

    return (
        <motion.button
            className={`share-btn ${className} ${copied ? 'copied' : ''}`}
            onClick={(e) => handleShare(e)}
            onTap={(e) => {
                e.stopPropagation();
                handleShare();
            }}
            onPointerDown={(e) => e.stopPropagation()}
            whileTap={{ scale: 0.97 }}
            aria-label={copied ? 'Link copied!' : 'Share results'}
            disabled={isSharing}
            data-clarity-action="share"
        >
            <AnimatePresence mode="wait" initial={false}>
                {copied ? (
                    <motion.span
                        key="copied"
                        className="share-btn-content"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        transition={{ duration: 0.15 }}
                    >
                        <Check size={18} aria-hidden="true" />
                        <span>Copied!</span>
                    </motion.span>
                ) : (
                    <motion.span
                        key="share"
                        className="share-btn-content"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        transition={{ duration: 0.15 }}
                    >
                        <Share2 size={18} aria-hidden="true" />
                        <span>Share</span>
                    </motion.span>
                )}
            </AnimatePresence>
        </motion.button>
    );
}

export default ShareButton;
