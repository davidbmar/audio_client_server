import { MobileNavBarTab } from "./mobile-nav-bar-tab";

export const MobileNavBarTabs = ({ handleClick }) => {
  return (
    <div className="mobile-nav-bar__tabs">
      <MobileNavBarTab
        path="/profile"
        label="Profile"
        handleClick={handleClick}
      />
      <MobileNavBarTab
        path="/public"
        label="Public"
        handleClick={handleClick}
      />
      <MobileNavBarTab
        path="/protected"
        label="Protected"
        handleClick={handleClick}
      />
      <MobileNavBarTab
        path="/admin"
        label="Admin"
        handleClick={handleClick}
      />
      <MobileNavBarTab
        path="/record"
        label="Record"
        handleClick={handleClick}
      />
      <MobileNavBarTab
        path="/file-manager"
        label="File Manager"
        handleClick={handleClick}
      /> {/* Add this block */}
    </div>
  );
};
