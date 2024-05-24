import { useAuth0 } from "@auth0/auth0-react";
import React, { useEffect, useState } from "react";
import { CodeSnippet } from "../components/code-snippet";
import { PageLayout } from "../components/page-layout";
import { getProtectedResource } from "../services/message.service";

export const RecordPage = () => {
  const [message, setMessage] = useState("");
  const { getAccessTokenSilently, user } = useAuth0();
  const [userId, setUserId] = useState("");

  useEffect(() => {
    let isMounted = true;

    const getMessage = async () => {
      const accessToken = await getAccessTokenSilently();
      const userIdValue = user.sub;
      setUserId(userIdValue);
      const { data, error } = await getProtectedResource(accessToken, userIdValue);

      if (!isMounted) {
        return;
      }

      if (data) {
        setMessage(JSON.stringify(data, null, 2));
      }

      if (error) {
        setMessage(JSON.stringify(error, null, 2));
      }
    };

    getMessage();

    return () => {
      isMounted = false;
    };
  }, [getAccessTokenSilently, user]);

  return (
    <PageLayout>
      <div className="content-layout">
        <h1 id="page-title" className="content__title">
          Recording Studio
        </h1>
        <div className="content__body">
          <p id="page-description">
            <span>
              This page retrieves a <strong>protected message</strong> from an
              external API.
            </span>
            <span>
              <strong>Only authenticated users can access this page.</strong>
            </span>
          </p>
          <p>
            <strong>User ID:</strong> {userId}
          </p>
          <CodeSnippet title="Protected Message" code={message} />
          <CodeSnippet title="Protected Message" code={userId} />
        </div>
      </div>
    </PageLayout>
  );
};
