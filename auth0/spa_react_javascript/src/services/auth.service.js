import { useAuth0 } from "@auth0/auth0-react";

export const useAuth = () => {
  const { getAccessTokenSilently, user } = useAuth0();
  const getUserId = () => user?.sub;
  return { getAccessTokenSilently, getUserId };
};

