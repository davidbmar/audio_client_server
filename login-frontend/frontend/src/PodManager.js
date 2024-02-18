import React, { useState, useEffect } from 'react';
import PodsTable from './PodsTable'; // Import the PodsTable component

const PodManager = ({ updateTrigger }) => {
    const [pods, setPods] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    // Define fetchPods at the component level
    const fetchPods = async () => {
        setIsLoading(true); // Consider setting loading true here if you want to indicate loading on refresh
        try {
            const response = await fetch('https://fmi6vgzxb1.execute-api.us-east-2.amazonaws.com/staging/listPods', {
                method: 'GET',
                headers: {
                    'x-api-key': '7cEGIf76VI31qPawLnbjJ3ix6LGuS8BJ51AleTwm',
                },
            });

            if (response.ok) {
                const jsonResponse = await response.json();
                console.log(jsonResponse); // Log for debugging
                const pods = jsonResponse.myself ? jsonResponse.myself.pods : [];
                setPods(pods);
            } else {
                console.error('HTTP error', response.status, await response.text());
            }
        } catch (error) {
            console.error('Fetch error:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchPods();
    }, [updateTrigger]); // Dependency array to re-fetch on updateTrigger changes

    const refreshPods = () => {
        setTimeout(() => {
            fetchPods(); // This now correctly calls the fetchPods function
        }, 3000); // Delay of 3 seconds
    };

    return (
        <div>
            {isLoading ? (
                <p>Loading...</p>
            ) : (
                <PodsTable pods={pods} onRefresh={refreshPods} />
            )}
        </div>
    );
};

export default PodManager;
