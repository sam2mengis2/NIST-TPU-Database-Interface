'use client';

import React, { useState } from 'react';

const WindAnalyzer = () => {
    const [file, setFile] = useState<File | null>(null);
    const [imageUrl, setImageUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleUpload = async () => {
        if (!file) return;
        
        setImageUrl(null); 
        setLoading(true);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://localhost:8000/files/upload', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            
            if (data.plot_url) {
                // Construct URL with timestamp to force refresh the image
                const filename = file.name.replace(/\.[^/.]+$/, "");
                const timestamp = new Date().getTime();
                setImageUrl(`http://localhost:8000/static/${filename}_3d_plt.png?v=${timestamp}`);
            }
        } catch (err) {
            console.error("Upload failed:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center space-y-6">
            <div className="p-4 border rounded shadow-sm bg-white w-full max-w-md">
                <input 
                    type="file" 
                    onChange={(e) => setFile(e.target.files?.[0] || null)} 
                    className="block w-full text-sm mb-4"
                />
                <button 
                    onClick={handleUpload}
                    disabled={!file || loading}
                    className="w-full bg-blue-600 text-white py-2 rounded font-bold disabled:bg-gray-400"
                >
                    {loading ? 'Uploading...' : 'Get Plot'}
                </button>
            </div>

            {imageUrl && (
                <div className="w-full max-w-4xl border p-2 bg-white shadow-lg">
                    <img 
                        src={imageUrl} 
                        alt="Wind Analysis Plot" 
                        className="w-full h-auto"
                    />
                </div>
            )}
        </div>
    );
};

export default WindAnalyzer;